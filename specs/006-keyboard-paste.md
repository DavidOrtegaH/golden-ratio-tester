# SPEC-006 — Paste instructions without a button

Remove the Paste image button from the shared upload area. Keep localized
Ctrl+V / Cmd+V instructions, image paste events, native file selection and their
shared preview. Remove the unused async clipboard read path and its tests.
No clipboard permission request is needed for the explicit native paste event.
