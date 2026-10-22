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

## Candidate first outcome

- Formal candidate invocation: **1/1**, retry 0. Exact command from `FREEZE.json`, using its resolved CPython 3.13.14 executable and working directory this package.
- Start UTC: `2026-10-12T02:08:54.7051628Z`; end UTC: `2026-10-12T02:09:03.9153013Z`; exit code: `0`.
- Candidate stdout/stderr: `A03-candidate.stdout.txt` / `A03-candidate.stderr.txt`; stderr is empty. Stdout SHA-256 `9caa321e00eaf9edac6d95117aad4a9d95864b4db5d8de1a3621f6e980b3cff2`; empty-stderr SHA-256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`.
- Runner reports allocation `UNJUNO-8636-ROTATION-FEATURES-T0-A03-20261012`, 360 trials, one candidate invocation.
- Candidate output before audit: 2,231 files / 63,489,719 bytes. `events.jsonl`: 2,588 rows, SHA-256 `118094d73082a7279bb8ab79e75c258a1d0edb7d31f02cea0effb4367cdcfa76`; `scorer_truth.jsonl`: 360 rows, SHA-256 `791dcc4dea92dec2b0067d0ac9004bcc17df33a43eee8fc8424022a90b3eab9f`.
- First-outcome archive: `A03-first-outcome.tar.gz`, 398,308 bytes, SHA-256 `60d6d0ae0b04ef58c006fef14b053dfda0c8077350510ac7e36f7c6541a1f229`. Independent byte comparison against all 2,231 manifest entries passed; `A03-candidate-manifest.json` SHA-256 is `789b68bfaf7c9e7d08ac90f33c25a449d3fad551d836cb61e10c8723f95a59e9`.
- At candidate completion, no method/hypothesis conclusion was assigned, and auditor invocations were 0/1. The candidate result was preserved before the one auditor command.

## Independent auditor first outcome

- Formal independent-auditor invocation: **1/1**, retry 0. Exact auditor command from `FREEZE.json`; start UTC `2026-10-12T02:10:39.9962255Z`, end UTC `2026-10-12T02:10:50.1277959Z`, exit code `1`.
- `A03-auditor.stdout.txt` is empty (SHA-256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`). `A03-auditor.stderr.txt` SHA-256 is `94a7c89f2e5af48c2a440b20f0e2ab4b939c01ab556b0b89cb0ebba3c4f6b4e9`.
- First failure: `auditor.py:268`, `ValueError: focal stress yield reason mismatch`, before `audit.json` was created. Formal disposition: `HOLD_UNCERTAIN`; no method or hypothesis result. Candidate raw archive, its byte manifest, and both process logs are preserved. No candidate or auditor retry is permitted for A03.
- A03 formal counters are candidate 1/1, auditor 1/1, retries 0/0. A separate read-only source/raw diagnosis may explain the mismatch but cannot upgrade or replace A03's first outcome.

This file is append-only after the freeze commit. Record each formal process once, with UTC start/end, exact invocation, stdout/stderr, exit status, and output custody. An uncertain command status is HOLD; do not reissue it.
