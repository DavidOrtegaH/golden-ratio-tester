# SPEC-008 — Public GitHub Pages application

Request: publish a usable public GitHub Pages link, add it to README, and remove
the requested entertainment references and authorship-tool discussion from README.

## Acceptance criteria

- Deploy the application, not just a repository landing page, under the project
  path on GitHub Pages over HTTPS. Verify deployment and a real image analysis.
- Keep the Django implementation runnable. Share the geometric detector with
  a browser Python/WebAssembly worker so Pages needs no external API or uploads.
- Keep Spanish/English, explicit language cookie, paste/upload in one area,
  result count, measured overlays, toggle, original-size PNG export and deletion.
- Host pinned runtime assets on the same Pages origin, verify package hashes
  during builds, document first-load cost and browser/runtime limitations.
- Responsive, keyboard-accessible interface; no reloads for the main workflow.
  Stop a stalled worker on timeout/cancel and release image/object URL resources.
- README opens with the public application link, remains in first person,
  keeps the learning section immediately after the app explanation, and clearly
  distinguishes browser processing from the optional Django server.
- Use English Conventional Commits and feature → develop → release → main.

## Validation

Run typechecking, existing unit tests, browser tests against the built Pages
artifact in Chromium/Firefox/WebKit, then verify the actual public deployment.
