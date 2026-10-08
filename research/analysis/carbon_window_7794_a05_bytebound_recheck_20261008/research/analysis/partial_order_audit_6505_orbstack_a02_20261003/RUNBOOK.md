# Runbook — Issue #6505 A02

The mount target is `results/audit_01/` and must be empty at process entry. Never write Docker configuration, stdout, inspect output, or host records there before the invocation. Save these under `execution/` or package root. `auditor.py` resolves its frozen manifest relative to its own source path.

Create a pinned-image container with network disabled, read-only repository/root filesystem, `/allocation` mounted read-only, and the empty `results/audit_01/` mounted writable at `/evidence`. Use the frozen CPU/memory/PID/capability/user settings in `FREEZE.json`. Save the exact `docker create` arguments and inspect output to `execution/` before start. Start once, capture stdout/exit status outside the mounted output (or after process exit), inspect once, and preserve all outputs. No retry, repair, or replacement allocation is allowed under A02.
