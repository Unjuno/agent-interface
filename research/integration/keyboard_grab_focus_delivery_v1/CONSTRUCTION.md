# Excluded construction

Formal rows: **0/20** at construction close.

Two declared construction cases passed:
- FOCUS_ONLY / CLEAR: A focus established, exact `7` inserted, no foreign key effect, terminal server input neutral.
- FOCUS_KEYBOARD_PROBE / GRAB_BEFORE_PROBE: A focus established before the foreign grab; probe returned AlreadyGrabbed/non-GrabSuccess; zero task-key emission and zero foreign key effect.

One additional excluded diagnostic confirmed that a foreign XGrabKeyboard acquired after the A-focus observation diverts a subsequent XTEST `7` press/release to the grab owner. Tk focus reporting became temporarily None under the active grab. This caused the pre-formal wording correction recorded on Issue #4159; no formal case or scientific threshold existed yet.

Raw construction JSON is retained outside the formal denominator; SHA-256: `3b9b87257e6e1275231dbb87006b1b6b9d320506b2208c4ec8b4c6ae9eb3e027`.
