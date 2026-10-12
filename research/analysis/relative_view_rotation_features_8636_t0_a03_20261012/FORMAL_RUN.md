# A03 formal execution record

## Pre-run gate

- Allocation: `UNJUNO-8636-ROTATION-FEATURES-T0-A03-20261012`.
- Frozen base main: `f185a9059d485a4f8d5a65e9e7f6782897f67eae`.
- Frozen package commit: recorded after freeze commit, before the first invocation.
- Candidate invocations before run: 0/1. Auditor invocations before run: 0/1. Retries: 0/0.
- Planned candidate output: `results/a03-outcome/` (must be absent or empty).
- Exact interpreter/commands and source checksums: `FREEZE.json`.
- No WSLc, Docker, GUI, model, OS input, network, or external application will be used.

Pre-run verification (2026-10-12): frozen source commit `9fe205e86e0cc136e2b7ede76a156598395a5698`, directly based on main `f185a9059d485a4f8d5a65e9e7f6782897f67eae`. Source-manifest test passes; construction suite passes 13/13 in normal and optimized modes; `py_compile` and `git diff --check` pass. The planned output path was absent. The formal runner and auditor had not been invoked.

This file is append-only after the freeze commit. Record each formal process once, with UTC start/end, exact invocation, stdout/stderr, exit status, and output custody. An uncertain command status is HOLD; do not reissue it.
