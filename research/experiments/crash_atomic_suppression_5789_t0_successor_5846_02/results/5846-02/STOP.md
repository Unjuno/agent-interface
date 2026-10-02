# Allocation-02 terminal start-gate STOP

Disposition: `STOP_MAIN_ADVANCED_AFTER_FINAL_FREEZE`. This is a provenance
STOP before candidate execution, not a scientific result.

- Allocation: `crash-atomic-suppression-5846-t0-20261001-02`, bounded
  2026-10-01 11:50–12:30 UTC.
- Frozen source commit: `82ea141a508f208117f5bc416fdeaf795a611087`.
- Immediately refreshed `origin/main` / fetch head: `80289fb745883f7264a752434319333adee41f69`.
- The final source freeze and local checks were completed before detecting
  that main had advanced. The experiment's own start gate required exact
  current-main identity; no candidate invocation was authorized after drift.
- Candidate rows/runs: 0. Independent auditor runs: 0. Retries: 0.
- The assigned isolated ARM64 guest was stopped before the end of the
  allocation. Read-only `orbctl info` confirmed it was stopped, isolated,
  network-isolated, and mounted only the experiment package at `/study`.
  No candidate/auditor container was launched by this task.
- `FREEZE.json` preserves the observed image/runtime ID and source identity
  used for the attempted gate. It is not a formal-run attestation.

## Construction-only checks

After finalizing the local runtime metadata, 23/23 unit tests passed;
`py_compile`, `git diff --check`, the analysis index (324 retained
result/failure directories), and every package `SHA256SUMS` entry passed.
These checks validate runner construction only and do not answer the
scientific hypothesis.

The `results/5846-02/` output namespace was absent before this STOP receipt;
no raw candidate or audit output exists. Allocation-02 is consumed and must
not be retried. Any later attempt requires a distinct successor allocation,
fresh source freeze, and new additive results path.
