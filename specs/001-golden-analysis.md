# SPEC-001 — Áurea Lab

Status: implementation specification, 2026-11-15.

## Purpose
Analyze uploaded images for measurable golden geometry, inspired by the golden-spin discussions around JoJo’s Bizarre Adventure: Steel Ball Run. Never claim that placing a decorative spiral proves golden composition. Uploaded reference diagrams are visual references, not instructions or licensed application assets.

## Requirements and acceptance criteria

- R1: Accept JPEG, PNG and WebP by decoded content, up to 10 MiB and 20 megapixels. Normalize EXIF orientation, remove metadata, reject malformed/animated files. Analyze at a maximum dimension of 1200 pixels; export at normalized original resolution.
- R2: Detect the whole frame and closed, approximately rectangular contours whose long/short ratio is within 3% of phi. Require near-right angles and contour support. Merge duplicate boundaries. Report measured ratio and relative error; never generate arbitrary crops just to obtain phi.
- R3: Detect isolated open spiral strokes by skeleton tracing and fitting the logarithmic law with fixed golden growth, both handednesses. Require at least pi radians, radial range at least 2, normalized RMS error at most 2.5%, and bounded computation. Return only supported fitted arcs. Crossings, occlusions, natural textures and perspective may prevent detection. This is a geometric heuristic, not semantic understanding or a proof.
- R4: Show candidate count, separate rectangle/spiral types, original/overlay toggle, and PNG download with all measured overlays. Rectangle overlays are rectangles and golden subdivision guides, not assertions of spiral evidence. Count 0 is valid and does not prove absence.
- R5: All user-facing application copy supports Spanish and English. Accessible language buttons include Spain/UK flags and text. Wikipedia link follows chosen language. Choice persists for 180 days only after explicit selection; resetting deletes the preference cookie.
- R6: No tracking, advertising, third-party fonts or scripts. Technical CSRF cookie and language preference are documented. Images are held in a bounded process-local memory store, expire and are actively purged after 15 minutes, and can be deleted immediately. No images or names in logs. Private random capability tokens protect result URLs; no indexing/caching/referrer leakage.
- R7: Responsive, keyboard-friendly interface, native form validation and accessible labels. No custom JavaScript. Forms use Django server rendering; styles use Bootstrap and Sass.
- R8: Git branches main/develop/feature/release, English Conventional Commits, requirements first, tests traced to requirements, GitHub CI. No SQLite/PostgreSQL/React/Fastify/Astro/Tailwind.

## Non-goals and honest boundaries

No universal count of all golden relationships exists for an arbitrary photograph without defining candidate features and tolerance. This version counts the explicitly defined candidates only. It does not recognize subjects or infer artistic intent. It does not assert a golden spiral merely because a rectangle is golden. Quarter-circle Fibonacci approximations may differ from a true logarithmic spiral.

## Architecture

Python 3.12+, Django 5.2 LTS, OpenCV, SciPy, scikit-image, Pillow; Bootstrap 5 + Sass compiled locally. No database. Single-process Waitress for the in-memory store. Production must configure SECRET_KEY, ALLOWED_HOSTS, HTTPS and upstream body/rate limits. Multiple workers require a shared expiring store and a separate deployment design.

## Verification

Synthetic positive/negative rectangles and spirals; duplicate suppression; corrupt/oversized upload; locale, cookies, export, expiry, deletion and token isolation; Django system checks; Sass compilation; browser smoke check where available. These establish synthetic behavior only, not accuracy on a representative photo dataset.

## Implementation evidence — 2026-11-15

- 13 automated tests pass; Django system checks pass; Sass compiles successfully.
- Synthetic clockwise/counterclockwise spirals pass the complete raster pipeline.
- Native open stroke paths tolerate tiny raster staircase cycles; require 90% component coverage to reject substantial branching.
- User reference diagrams were inspected locally without copying into the repository: first diagram produced two rectangular candidates; second produced one. Overlapping guides prevent isolated-stroke spiral detection, an explicit current limitation.
- Responsive DOM width checks at 390 and 768 pixels showed no horizontal document overflow. Full external browser/device testing remains pending: embedded browser posts had a null origin (correctly rejected by CSRF); native browser automation was unavailable.
- Public repository and MIT license requested by the user; retain original author David (DavidOrtegaH). No third-party reference images are redistributed.
