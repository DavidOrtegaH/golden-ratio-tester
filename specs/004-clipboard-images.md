# SPEC-004 — Paste a copied image

- Support Ctrl+V / Cmd+V of clipboard image files on the upload page, plus a
  Paste image button where navigator.clipboard.read is supported and permitted.
- Display a local preview and live confirmation before analysis. Pasting never
  submits or uploads automatically. File selection replaces pasted input and vice versa.
- Both paths populate the same native image input and submit the existing CSRF
  protected multipart form. Backend validation and privacy guarantees remain.
- Reject oversized/unsupported clipboard files, handle empty/text-only clipboard,
  unsupported browsers and denied permission with localized guidance. Never fetch
  URLs from clipboard text/HTML. Read clipboard only on explicit paste/click.
- Keep Spanish and English copy, keyboard access and responsive layout. File
  selection continues working without scripts.
- Use TypeScript with Stimulus (framework) and esbuild; this supersedes the earlier
  no-client-JavaScript implementation requirement while honoring the requested
  framework approach. CSP permits self-hosted scripts and blob image previews,
  with no inline scripts or external scripts.
- Verify paste/file replacement, preview cleanup, errors, button reads and native
  form submission integration; retain Django flow/CSRF checks.
