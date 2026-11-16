# Contributing

Original author: David (GitHub: DavidOrtegaH). Contributions are welcome under MIT.

Use specification-driven development (SpecDD): propose or update a requirement in
`specs/` before implementation; add acceptance tests that cite its requirement ID;
implement; run the checks; record evidence and limitations in the specification.

Branches: `feature` → `develop` → `release` → `main`. Use pull requests for subsequent
changes and English Conventional Commits, e.g. `feat: detect rotated golden rectangles`.
The initial release is fast-forwarded across the four branches after validation.

Run `npm ci`, `npm run build`, `npm run typecheck`, `npm test`,
`python manage.py check`, and `python manage.py test` with `DJANGO_DEBUG=1`.
Run `npm run test:e2e` after installing Playwright browsers for workflow/UI changes.
For the public Pages application, run `npm run build:pages` and `npm run test:pages`.
Review `pages/package-profile.json` before adding detector imports; the browser
runtime deliberately excludes unused image codecs and plotting dependencies.
Use Node 22.22.2+ or 24.15+ for the test dependencies.
Do not commit uploads, tokens, personal filenames, secrets, or downloaded reference art.
Do not claim measured accuracy on photographs without a labeled validation dataset.
