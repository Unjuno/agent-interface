# Run ledger

## Freeze

- Frozen current-main snapshot: `b54ec8fac5d005d510a5787d98b9ad7a24d96923`.
- Historical preregistration path: `research/doom/map01_measurement_integration_live_v2_prereg.json`.
- Historical allocation recorded by that preregistration: `map01-measurement-integration-live-02`; no invocation under that ID is made.
- Local execution: Windows host, CPython 3.12; candidate and auditor read only Git object blobs from the local repo object database. The task fetched current main before freeze; candidate/auditor make no network requests.
- The latest #5085 records do not assign this task an exclusive Docker/OrbStack or GPU slot; unrelated task releases/leases are not inherited. Shared Docker inventory remains UNKNOWN, so container/game/model work is excluded.

## Pre-formal construction checks

- `python -m unittest -v test_construction.py`: initial run **FAIL, 2/4** because the pinned-drift negative controls kept a stale candidate fixture instead of reflecting the altered raw source. The formal candidate had not run; both defects were in the test fixture.
- After correcting the negative-control fixture, `python -m unittest -v test_construction.py`: **4/4 PASS**.
- `python -m py_compile candidate.py auditor.py`: PASS.
- `git diff --check`: PASS.
- Before the candidate invocation, `candidate_output.json` and `audit.json` were absent. Frozen implementation/input SHA-256 values are recorded in `SHA256SUMS`.

## One-shot source inventory candidate

- Invoked exactly once from the package working directory with command `python candidate.py --repo-root ..\..\..\..\..\..\_clean_main_20261001 --out candidate_output.json`.
- Exit 1 before reading the frozen preregistration: the relative repository-root path overshot the repository. Git returned status 128 for the missing repo path; traceback is retained in `STOP.json`.
- Disposition: `STOP_RUNNER_REPO_ROOT`; source inventory was **NOT_EVALUATED**. No candidate output was created.
- This one-shot invocation is not retried. Independent auditor invocations: **0**.

## Independent raw audit

Pending.

## Scope / stop state

No live allocation, Actions dispatch, Docker/OrbStack, ViZDoom, model, GPU, GUI, or OS-input operation is authorized or attempted by this source-closure study. The source hypothesis is unevaluated; the infrastructure STOP does not refresh the historical allocation or authorize recovery-vs-coast efficacy work. Any successor must use a fresh additive path and robustly resolve the repository root before its own one-shot freeze/run.
