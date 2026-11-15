# SPEC-003 — Evidence from photographic contours

Extend detection beyond isolated binary strokes. Preserve the original upload,
privacy, locale, export and CSRF behavior.

- Extract ordered Canny contours at two blur scales; examine bounded overlapping
  portions, so intersections and unrelated connected edges do not require the
  entire connected component to be one spiral.
- Estimate a free logarithmic growth parameter before accepting golden growth.
  Require substantial angular extent, low residual, growth near the golden law,
  and aligned image gradients across the fitted arc. Reject circles and constant
  spacing spirals. Deduplicate alternate boundaries of one physical stroke.
- Display measured growth and contour support, with metrics distinguished from
  rectangle aspect ratio. These are geometric candidates, not object recognition.
- Validate transformed/textured/occluded synthetic examples, circles, non-golden
  spirals and photographic controls. Record real source provenance and results;
  never label a photograph golden merely because its title says so.
- Keep computation bounded by image size, contour and fit budgets. Record runtime.

The original synthetic tests remain regression tests. A small development sample
is not a statistically representative accuracy benchmark.
