"""Conservative, bounded geometric candidates; no semantic or aesthetic claims."""
from dataclasses import dataclass
from collections import deque
import math
import cv2
import numpy as np
from scipy.optimize import least_squares
from skimage.morphology import skeletonize

PHI = (1 + math.sqrt(5)) / 2
GROWTH = 2 * math.log(PHI) / math.pi


@dataclass
class Candidate:
    kind: str
    points: list
    error: float
    ratio: float = PHI
    growth: float | None = None
    support: float | None = None
    metric: str = 'radial'
    model: tuple | None = None


def rectangle(points, kind='rectangle'):
    p = np.asarray(points, dtype=float)
    edges = np.roll(p, -1, axis=0) - p
    lengths = np.linalg.norm(edges, axis=1)
    if lengths.min() < 30:
        return None
    cosines = np.sum(edges * np.roll(edges, -1, axis=0), axis=1) / (lengths * np.roll(lengths, -1))
    if np.max(np.abs(cosines)) > 0.09:
        return None
    sides = (lengths[:2] + lengths[2:]) / 2
    ratio = sides.max() / sides.min()
    error = abs(ratio / PHI - 1)
    if error > 0.03:
        return None
    return Candidate(kind, p.tolist(), error * 100, float(ratio))


def rectangles(rgb):
    height, width = rgb.shape[:2]
    candidates = []
    frame = rectangle([[0, 0], [width - 1, 0], [width - 1, height - 1], [0, height - 1]], 'frame')
    if frame:
        candidates.append(frame)
    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    edges = cv2.Canny(cv2.GaussianBlur(gray, (5, 5), 0), 60, 160)
    contours, _ = cv2.findContours(edges, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    for contour in sorted(contours, key=cv2.contourArea, reverse=True)[:300]:
        if cv2.contourArea(contour) < max(900, width * height * 0.001):
            continue
        poly = cv2.approxPolyDP(contour, 0.015 * cv2.arcLength(contour, True), True)
        if len(poly) != 4 or not cv2.isContourConvex(poly):
            continue
        candidate = rectangle(poly[:, 0])
        if not candidate:
            continue
        # Both sides of a thick outline should produce one candidate.
        p = np.asarray(candidate.points, np.float32)
        duplicate = False
        for previous in candidates:
            q = np.asarray(previous.points, np.float32)
            intersection, _ = cv2.intersectConvexConvex(p, q)
            union = cv2.contourArea(p) + cv2.contourArea(q) - intersection
            if union and intersection / union > 0.80:
                duplicate = True
                break
        if not duplicate:
            candidates.append(candidate)
    return candidates


def fit_spiral(points):
    """Fit known golden growth to an ordered, continuous, open stroke."""
    p = np.asarray(points, dtype=float)
    p = p[np.linspace(0, len(p) - 1, min(160, len(p))).astype(int)]
    span = float(np.linalg.norm(np.ptp(p, axis=0)))
    if span < 60:
        return None
    origin = p.min(axis=0)
    normalized = (p - origin) / span
    best = None
    for sign in (-1, 1):
        b = sign * GROWTH

        def residual(center):
            delta = normalized - center
            radius = np.maximum(np.linalg.norm(delta, axis=1), 1e-6)
            theta = np.unwrap(np.arctan2(delta[:, 1], delta[:, 0]))
            a = np.mean(np.log(radius) - b * theta)
            predicted = np.exp(np.clip(a + b * theta, -15, 5))
            return radius - predicted

        for seed in (normalized[0], normalized[-1], normalized.mean(axis=0)):
            result = least_squares(residual, seed + 0.01, bounds=(-1.5, 2.5), max_nfev=80)
            center = result.x
            delta = normalized - center
            radius = np.linalg.norm(delta, axis=1)
            theta = np.unwrap(np.arctan2(delta[:, 1], delta[:, 0]))
            angle = abs(theta[-1] - theta[0])
            variation = np.abs(np.diff(theta)).sum()
            error = float(np.sqrt(np.mean(residual(center) ** 2)))
            if not (math.pi <= angle <= 5 * math.pi and variation <= angle * 1.08
                    and radius.min() > 0.005 and radius.max() / radius.min() >= 2
                    and error <= 0.025):
                continue
            if best is None or error < best.error / 100:
                a = np.mean(np.log(radius) - b * theta)
                t = np.linspace(theta[0], theta[-1], 240)
                r = np.exp(a + b * t)
                fitted = (center + np.column_stack((r * np.cos(t), r * np.sin(t)))) * span + origin
                best = Candidate('spiral', fitted.tolist(), error * 100)
    return best


def spirals(rgb):
    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    if np.count_nonzero(binary) > binary.size / 2:
        binary = 255 - binary
    skeleton = skeletonize(binary > 0).astype(np.uint8)
    count, labels, stats, _ = cv2.connectedComponentsWithStats(skeleton, 8)
    found = []
    components = sorted(range(1, count), key=lambda i: stats[i, cv2.CC_STAT_AREA], reverse=True)[:24]
    for label in components:
        if not 90 <= stats[label, cv2.CC_STAT_AREA] <= 12000:
            continue
        ys, xs = np.where(labels == label)
        pixels = set(zip(xs.tolist(), ys.tolist()))

        def neighbors(point):
            x, y = point
            # Ignore diagonal shortcuts when an orthogonal connection exists.
            return [(x + dx, y + dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1)
                    if (dx or dy) and (x + dx, y + dy) in pixels
                    and not (dx and dy and ((x + dx, y) in pixels or (x, y + dy) in pixels))]

        ends = [point for point in pixels if len(neighbors(point)) == 1]
        if len(ends) != 2:
            continue
        # Pixel staircases may contain tiny cycles; trace between endpoints
        # through those cycles instead of mistaking them for real branches.
        parents = {ends[0]: None}
        queue = deque([ends[0]])
        while queue:
            current = queue.popleft()
            for following in neighbors(current):
                if following not in parents:
                    parents[following] = current
                    queue.append(following)
        path, current = [], ends[1]
        while current is not None:
            path.append(current)
            current = parents[current]
        if len(path) < len(pixels) * 0.90:
            continue
        from .contours import fit_contour
        candidate = fit_contour(path)
        if candidate:
            found.append(candidate)
    return found


def analyze(image):
    from .contours import photographic_spirals
    from .templatesearch import edge_spirals
    width, height = image.size
    scale = min(1, 1200 / max(width, height))
    small = image.resize((round(width * scale), round(height * scale)))
    rgb = np.array(small)
    strokes = spirals(rgb)
    curves = strokes + photographic_spirals(rgb, strokes)
    curves += edge_spirals(rgb, curves)
    candidates = rectangles(rgb) + curves
    sx, sy = width / small.width, height / small.height
    for candidate in candidates:
        candidate.points = [[x * sx, y * sy] for x, y in candidate.points]
        if candidate.model:
            x, y, b, a = candidate.model
            candidate.model = (x * sx, y * sy, b, a + math.log(math.sqrt(sx * sy)))
    return candidates
