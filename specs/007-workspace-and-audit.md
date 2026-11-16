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
