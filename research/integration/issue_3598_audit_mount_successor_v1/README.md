# Issue #3598 — correctly mounted frozen raw audit

This is a new audit-only successor after two preserved outcomes:

1. #3587's original three public-MCP allocations have an official frozen-v1
   audit result of `HOLD_OR_FAIL`.
2. #3595's v2 auditor stopped before reading allocation JSON because its
   required frozen parent files were not visible beside the mounted `freeze/`
   directory.

Neither predecessor is changed or upgraded. #3598 reuses the exact hash-pinned
#3595 auditor, mounts the complete parent directory at `/parent`, and runs one
no-network raw reconstruction audit against the same read-only allocations.
It creates no GUI, Xvfb, runtime, or input evidence.

The exact #3595 startup failure is retained in `STOP_3595.json`. The
hash-pinned preflight and one formal audit are separate. Preflight passed in
the pinned container; the single formal raw audit has not yet started.
