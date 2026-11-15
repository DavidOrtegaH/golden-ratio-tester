# SPEC-005 — One shared image area

Place file selection, clipboard action, paste instructions, status and preview
inside one bordered upload area. Label it Upload or paste an image in both
languages. Preserve native file selection, the existing clipboard controller,
CSRF submission and the single selected image/preview state. No second paste box.

Validation: six Django flow tests pass. Browser inspection confirms one upload
area containing the file input, clipboard button and shared preview. The existing
Stimulus controller is unchanged.
