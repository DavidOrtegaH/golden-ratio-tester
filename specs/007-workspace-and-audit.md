# SPEC-007 — Golden Ratio Tester: one screen and audit

User request, 2026-11-16: keep image input, analysis, results, guide toggle,
download, deletion and language changes on the same screen, avoiding reloads
where supported; complete naming, compatibility, security/usability audit and
rewrite the README with a personal technical learning section.

## Acceptance criteria

- Enhanced forms use same-origin fetch + FormData with CSRF; server returns
  JSON and an escaped result fragment. No upload on paste/selection. Normal
  forms remain a working fallback. Results render in the existing workspace.
- Busy state, duplicate prevention, localized recoverable errors, keyboard
  focus and live announcements. Guide toggle is local. A new selection clears
  stale results. Language changes preserve the selected image and results.
- Bound request body/file/field counts and streaming file memory before decode.
  Rate-limit expensive analysis with bounded, expiring state. Keep image
  normalization and timed deletion. Redact capability URLs in application logs.
- JSON errors for CSRF, payload limits, expired results and processing failures;
  generic localized error pages as HTML fallback. Restrictive self-only CSP,
  no inline script/eval and no third-party runtime requests.
- Production defaults fail closed without a secret; development setup remains
  documented. Preserve the explicitly bounded local preview origin exception.
- Golden Ratio Tester in application, Python package, cookies, downloads,
  documentation and GitHub repository metadata/name. Preserve a migration path
  for the user's previously selected locale. Historic specifications identify
  their original paths where needed.
- README in the owner's requested first-person voice, with explanation followed
  by learning, solutions and achievements grounded in implemented project work.
  Include accurate setup, limits, privacy, verification and license information.
- Test relevant frontend interactions, backend failures/limits and image flow;
  record browser/device verification limits and audit findings candidly.

## Completed verification — 2026-11-17

- Single-document workflow verified in Chromium, Firefox and WebKit: 12 browser
  cases passed, with no unexpected failures. Includes responsive widths 390/768/1280,
  normal-form fallback, locale preservation, download and deletion.
- 33 backend cases (32 full-suite cases plus the added production secret guard
  exercised in the updated security suite) and 11 frontend cases passed.
- axe checks of the tested result page: no detected A/AA violations. This does
  not certify every state, device or assistive technology.
- Pillow updated to 13.0.0. Final pinned-runtime pip-audit and npm audit: no known
  vulnerabilities reported. Production boot guards, static collection and
  deployment checks exercised; two domain-dependent HSTS decisions remain.
- Repository renamed to DavidOrtegaH/golden-ratio-tester; Python package and locale
  cookie renamed, retaining only explicit migration references to previous names.
- README rewritten as requested, with project-grounded learning/solutions/results.
  Audit scope, evidence and remaining limitations: docs/audit-2026-11-17.md.
