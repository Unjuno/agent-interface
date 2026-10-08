# X11 unsupported verification preflight

The X11 backend previously treated a `verify` predicate as a successful no-op.
It now rejects any program containing that unsupported operation during preflight,
before executing the program prefix. The shared syntax remains valid; static
validation does not establish backend support or application-level success.
Callers must observe and explicitly review the application state.

The regression failed before the change (before.log). The first candidate run
retains a separate ambient-display punctuation failure: colon became apostrophe
(after.log). A fresh private Xvfb run passes all 22 partial-execution/integration
tests (private-xvfb.log), including independent save-file verification after a
refused program and successful subsequent dispatch. This does not establish why
the ambient layout failed or claim to fix it.

The native suite passed (native-result.json). Its initial launch failed because
the output directory had been pre-created; the corrected launch used a new output
directory. No GUI allocation or frozen experiment was repeated.

These are programmatic tests, not a fresh primary-model visual self-use trial.
No latency, model-token, cost, or human-speed improvement is claimed.
