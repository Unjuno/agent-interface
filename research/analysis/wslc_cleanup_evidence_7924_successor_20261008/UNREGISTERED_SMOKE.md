# Unregistered one-shot environment smoke — preserved as STOP

This record is deliberately separate from the frozen offline receipt-contract study below. The environment smoke was run before a new H/T/D/C/U protocol or allocation freeze existed; it is **not** a formal A05 allocation and is not retroactively preregistered.

- Command: `& .\.github\scripts\test_wslc_local_runtime.ps1`
- Main/source base: `6ea1269defb6d48a607f13b08f1aa2d223ba06e9`.
- Executed smoke source: `.github/scripts/test_wslc_local_runtime.ps1`, Git blob `a3c6eda97fb4260c94091240964afdcc1538d7f5`, SHA-256 `06D952B7CC8799C1FDCFF8FFD1FD6B0DC30FCB14F2E9442FC0F7BDD700B31459`.
- Candidate script invocation: 1; exit code: 1. Auditor: 0. Retry: 0.
- WSL / WSLc reported `3.0.1.0`; pinned image: `python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`.
- The isolated Python process verified the read-only bind by receiving `EROFS` on a write attempt. The kernel warned swap-limit/cgroup support is unavailable; no hard memory-limit result is claimed.
- The exact-ID scoped cleanup query exited 0, but the script rejected its returned value at line 83: `The scoped WSLc cleanup query did not return an empty JSON array; cleanup is unverified.`
- Final disposition: `STOP_CLEANUP_UNVERIFIED`. This is not a WSLc runtime PASS and not a Docker comparison.

## Evidence limitation

The original script removed its GUID temporary directory in `finally`, including `container.cid`, and did not print the raw scoped-list response before throwing. Therefore neither the container ID nor query output is available in the retained command result. `--rm` was requested, but actual cleanup was not independently verified. Do not infer that the container is present or absent. No global list, unrelated ID lookup, stop, delete, or repeat invocation was performed.

The tool output also rendered the WSL version text with embedded NUL/replacement characters, so only the readable WSLc version and the script's subsequent successful progress are used here. The lost query response cannot be reconstructed from this transcript.

The follow-up adds receipt retention and validates its pure classifier offline only. It does not close this STOP. Any future WSLc operation requires explicit reconciliation of the possibly unverified owned container/lane state and a newly frozen successor.
