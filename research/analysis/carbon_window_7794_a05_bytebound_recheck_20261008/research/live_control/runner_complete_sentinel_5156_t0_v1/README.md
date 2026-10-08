# Issue #5156 completion-sentinel mutation experiment

This is a Docker/OrbStack construction-boundary experiment against the actual
independent auditor from PR #5630, not a formal X11 allocation. It uses only
synthetic JSONL and the Python standard library.

The experiment feeds an unchanged integer-zero completion control and eight
preregistered mutations through the auditor CLI in separate child processes.
The candidate and independent raw-only audit run in separate digest-pinned,
network-disabled containers when the named local slot is granted and passes
its immediate pre-run gate. No Docker launch is allowed outside that slot.

The hypothesis concerns Python type-coercion and completion-row cardinality:
`False` and `0.0` compare equal to integer `0`, and an additional nonzero
completion record may not be counted by the current success-only filter. The
other mutations test malformed, missing, and duplicate completion evidence.

Limits: no X server, XTEST, physical input, MAP01/game, model, GPU, application
consumption, task effect, or formal #5156 result is exercised or claimed.
