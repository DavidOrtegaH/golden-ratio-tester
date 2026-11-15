# SPEC-002 — Golden Ratio Tester and local embedded forms

User request: rename the app and fix the reported null-origin CSRF failure.

- Display Golden Ratio Tester in the header, title, documentation and downloads.
- Permit the embedded browser's literal `Origin: null` only in DEBUG mode, over
  HTTP, when both the validated host and direct client address are loopback.
- Continue requiring a matching CSRF cookie and form token for every unsafe request.
- Reject null origins in production, for non-loopback clients/hosts and over HTTPS.
  Other origins retain Django's default checks. Do not add null to trusted origins.
- Use same-origin referrers so HTTPS browsers without Origin can pass Django's
  Referer check without leaking private result URLs to external destinations.
- Verify missing/wrong tokens, normal origins, local null-origin upload, language
  and delete, and production rejection. Keep the longer brand usable on mobile.

Validation: all 15 tests pass; Django system checks pass; Sass compiles.
This supersedes SPEC-001’s initial null-origin preview limitation.
