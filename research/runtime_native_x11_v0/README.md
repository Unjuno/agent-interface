# Native X11 backend v0

This is a real Linux/X11 backend integration experiment stacked on the compiled semantic core in PR #101. It runs only inside a private Xvfb display and does not modify the promoted runtime.

The backend dynamically loads XTest at runtime, reports missing injection support as capability absence, and binds semantic admission to real X11 focus, capture, pointer/keyboard delivery and release verification.

Current v0 deliberately leaves `input.text` and `event.feedback` unsupported. Therefore it is **not office-ready**. The experiment includes an `unsupported_text` condition that must fail before any X input; unsupported capability is evidence, not a feature to hide.

The independent fixture ledger is not consumed by the controller while input is active. A separate scorer reads it after input ends.
