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

## Final thresholds and budgets

- Contour proposals: at least π angular span, radius ratio ≥2.3, free-growth b
  within 8% of golden b, free radial RMS ≤1.2%, golden radial RMS ≤1.8%.
- Fragmented-edge template proposals: one full turn; independently refine growth
  and reject b outside 8%; golden edge-distance RMS ≤1.2% of arc diagonal.
- Both photographic routes: ≥72% nearby edge points with normal agreement,
  ≥40% evidence in every eighth of the arc. Tolerance max(2px, 0.8% diagonal).
- Template coarse search: 9×9 centers, 7 radii, 24 angles, both handednesses;
  refine best 48 proposals. Contour budget: 160 fits at each of two blur scales.
- Merge overlapping arcs and compatible center/phase models. Counts represent
  candidate segments, potentially several per physical structure.
- A 270° template experiment produced a suspicious candidate on the astronaut
  control and was discarded; the final template method requires a full 360°.

No downloaded third-party photo is tracked in Git. External source links and
licenses are retained in the evaluation script/report. Source specification
SPEC-001 remains historical where superseded by this specification.

## Verification evidence

19 automated tests passed. The local real-HTTP flow passed with the unmodified
2395×1588 shell photograph: two segments, growth/support display, hidden guides,
original-resolution PNG download, English translation and null-origin CSRF.
Baseline comparison and source provenance are recorded in docs/detector-evaluation.md.
The photograph itself and its annotated derivative are kept outside Git with
CC BY-SA 4.0 attribution; the code remains MIT.
