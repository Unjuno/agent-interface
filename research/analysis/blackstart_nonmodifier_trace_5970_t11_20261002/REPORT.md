# Issue #5970 T11 — non-modifier control

## Disposition

`HOLD_NONMODIFIER_STREAM_DIVERGENCE` (independent raw audit). Initial A keymap was neutral. The exact T3-derived app logged one `a` KeyPress and one KeyRelease (keycode 38); the parent-only observer selected XID 2097170 and logged three events, including an extra KeyRelease at the press timestamp. X RECORD retained five delivery records on that XID. Cleanup release was attempted and terminal A keymap was neutral. This matches the extra-release pattern from Shift, so the modifier-specific hypothesis was not supported.

The exact cross-stream gate did not pass; no rows were removed. Python-Xlib teardown raised `TypeError("cannot convert 'NoneType' object to bytes")` after capture and is retained. One private-Xvfb fixture only; no deployed #4135, physical-input, production, generalized provenance, recovery or task-benefit claim. Docker Desktop unavailable; WSL2/Xvfb fallback.
