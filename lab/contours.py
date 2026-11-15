"""Bounded proposals from ordered photographic edges, independently fitted growth."""
import math
import cv2
import numpy as np
from scipy.optimize import least_squares
from scipy.ndimage import gaussian_filter1d
from scipy.spatial import cKDTree

from .geometry import Candidate, GROWTH


def fit_contour(points):
    p = np.asarray(points, dtype=float)
    p = p[np.linspace(0, len(p) - 1, min(100, len(p))).astype(int)]
    smooth = gaussian_filter1d(p, 2, axis=0)
    tangents = np.diff(smooth, axis=0)
    heading = np.unwrap(np.arctan2(tangents[:, 1], tangents[:, 0]))
    turning = abs(heading[-1] - heading[0])
    if turning < 2.0 or np.abs(np.diff(heading)).sum() > turning * 1.5:
        return None
    origin = p.min(axis=0)
    span = np.linalg.norm(np.ptp(p, axis=0))
    if span < 80:
        return None
    p = (p - origin) / span
    best = None
    for sign in (-1, 1):
        def residual(parameters):
            center, b = parameters[:2], parameters[2]
            delta = p - center
            r = np.maximum(np.linalg.norm(delta, axis=1), 1e-6)
            theta = np.unwrap(np.arctan2(delta[:, 1], delta[:, 0]))
            a = np.mean(np.log(r) - b * theta)
            return r - np.exp(np.clip(a + b * theta, -15, 5))

        for seed in (p[0], p[-1], p.mean(axis=0)):
            fit = least_squares(residual, [*(seed + 0.01), sign * GROWTH],
                                bounds=([-1.5, -1.5, -0.8], [2.5, 2.5, 0.8]), max_nfev=45)
            center, b = fit.x[:2], fit.x[2]
            delta = p - center
            radius = np.linalg.norm(delta, axis=1)
            theta = np.unwrap(np.arctan2(delta[:, 1], delta[:, 0]))
            angle = abs(theta[-1] - theta[0])
            error = float(np.sqrt(np.mean(residual(fit.x) ** 2)))
            growth_error = abs(abs(b) / GROWTH - 1)
            if (angle < math.pi or angle > 5 * math.pi
                    or np.abs(np.diff(theta)).sum() > angle * 1.06
                    or radius.min() < .008 or radius.max() / radius.min() < 2.3
                    or error > .012 or growth_error > .08):
                continue
            a = np.mean(np.log(radius) - b * theta)
            t = np.linspace(theta[0], theta[-1], 240)
            # Render the actual golden law, not the fitted non-golden law.
            golden_b = math.copysign(GROWTH, b)
            golden_a = np.mean(np.log(radius) - golden_b * theta)
            golden_r = np.exp(golden_a + golden_b * theta)
            golden_error = float(np.sqrt(np.mean((radius - golden_r) ** 2)))
            if golden_error > .018:
                continue
            r = np.exp(golden_a + golden_b * t)
            curve = (center + np.column_stack((r * np.cos(t), r * np.sin(t)))) * span + origin
            candidate = Candidate('spiral', curve.tolist(), golden_error * 100,
                                  growth=math.exp(abs(b) * math.pi / 2),
                                  model=(*(center * span + origin), golden_b, golden_a + math.log(span)))
            if best is None or candidate.error < best.error:
                best = candidate
    return best


def supported(candidate, gray, edges):
    """Require nearby edge evidence AND normal agreement along the whole arc."""
    points = np.asarray(candidate.points)
    h, w = gray.shape
    indices = np.rint(points).astype(int)
    valid = (indices[:, 0] >= 0) & (indices[:, 0] < w) & (indices[:, 1] >= 0) & (indices[:, 1] < h)
    if valid.mean() < .98:
        return False
    ys, xs = np.where(edges)
    if not len(xs):
        return False
    tree = cKDTree(np.column_stack((xs, ys)))
    distances, nearest = tree.query(points)
    gx = cv2.Sobel(gray, cv2.CV_32F, 1, 0)
    gy = cv2.Sobel(gray, cv2.CV_32F, 0, 1)
    normals = np.column_stack((gx[ys[nearest], xs[nearest]], gy[ys[nearest], xs[nearest]]))
    tangents = np.gradient(points, axis=0)
    aligned = np.abs(np.sum(tangents * normals, axis=1)) / np.maximum(
        np.linalg.norm(tangents, axis=1) * np.linalg.norm(normals, axis=1), 1e-6) < .55
    tolerance = max(2.0, np.linalg.norm(np.ptp(points, axis=0)) * .008)
    hits = (distances <= tolerance) & aligned
    coverage = float(hits.mean())
    if coverage < .72 or min(part.mean() for part in np.array_split(hits, 8)) < .40:
        return False
    candidate.support = coverage * 100
    return True


def duplicate(candidate, others):
    p = np.asarray(candidate.points)
    for other in others:
        q = np.asarray(other.points)
        scale = max(np.linalg.norm(np.ptp(p, axis=0)), np.linalg.norm(np.ptp(q, axis=0)))
        if candidate.model and other.model:
            cx, cy, b, a = candidate.model
            ox, oy, ob, oa = other.model
            period = 2 * math.pi * GROWTH
            phase_difference = abs((a - oa + period / 2) % period - period / 2)
            if (b * ob > 0 and math.hypot(cx - ox, cy - oy) < scale * .05
                    and phase_difference < .08):
                return True
        # Bidirectional partial overlap merges duplicate stroke boundaries while
        # keeping separate spirals at different positions/scales.
        forward = (cKDTree(q).query(p)[0] < scale * .035).mean()
        backward = (cKDTree(p).query(q)[0] < scale * .035).mean()
        if min(forward, backward) > .35 and max(forward, backward) > .85:
            return True
    return False


def photographic_spirals(rgb, existing=()):
    scale = min(1, 800 / max(rgb.shape[:2]))
    small = cv2.resize(rgb, None, fx=scale, fy=scale) if scale < 1 else rgb
    gray = cv2.cvtColor(small, cv2.COLOR_RGB2GRAY)
    found = []
    for sigma in (1.2, 2.4):
        budget = 160
        blurred = cv2.GaussianBlur(gray, (0, 0), sigma)
        edges = cv2.Canny(blurred, 35, 100)
        contours, _ = cv2.findContours(edges, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)
        for contour in sorted(contours, key=len, reverse=True)[:50]:
            p = contour[:, 0].astype(float)
            if len(p) < 140 or np.linalg.norm(np.ptp(p, axis=0)) < 80:
                continue
            # Closed edge outlines have a turning point at the stroke tip.
            # Overlapping windows can recover a long uninterrupted side.
            for fraction in (.5, .375, .75, 1.0):
                length = round(len(p) * fraction)
                if length < 140:
                    continue
                for start in np.unique(np.linspace(0, len(p) - length, 9).astype(int)):
                    window = p[start:start + length]
                    # Only spend optimization budget on smooth, consistently
                    # turning paths, rather than stair treads or texture noise.
                    smooth = gaussian_filter1d(window[np.linspace(0, len(window)-1, 100).astype(int)], 2, axis=0)
                    tangent = np.diff(smooth, axis=0)
                    heading = np.unwrap(np.arctan2(tangent[:, 1], tangent[:, 0]))
                    turn = abs(heading[-1] - heading[0])
                    if turn < 2 or np.abs(np.diff(heading)).sum() > turn * 1.5:
                        continue
                    budget -= 1
                    candidate = fit_contour(window)
                    if candidate and supported(candidate, blurred, edges):
                        candidate.points = (np.asarray(candidate.points) / scale).tolist()
                        if candidate.model:
                            x, y, b, a = candidate.model
                            candidate.model = (x / scale, y / scale, b, a - math.log(scale))
                        if not duplicate(candidate, [*existing, *found]):
                            found.append(candidate)
                    if budget <= 0:
                        break
                if budget <= 0:
                    break
            if budget <= 0:
                break
    return found[:12]
