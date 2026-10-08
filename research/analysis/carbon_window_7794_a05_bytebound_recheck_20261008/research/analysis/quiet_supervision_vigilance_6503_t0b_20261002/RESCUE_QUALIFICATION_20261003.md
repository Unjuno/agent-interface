# Rescue qualification — Issue #6503 T0b preparation (2026-10-03)

This is an additive custody transfer of the 10-file preformal package from
`research/quiet-supervision-vigilance-6503-t0b-orbstack-20261002` at source head
`1332895c34fd588d0e2b2399dae8c54eb44f4bde`. The original package files are
preserved byte-for-byte. This note and the CI wiring below are additions; they
do not turn the preparation package into a formal result.

## Checks and integration scope

- The package's 15 construction/scorer tests pass locally under CPython 3.14.5.
  They exercise synthetic in-memory material and scripted scoring; they do not
  invoke `run_candidate.py` or `run_auditor.py`.
- The old branch's Analysis Index workflow snapshot was stale relative to
  current `main`: taking it wholesale would remove eight existing test steps
  for other Issues. Only its single additive #6503 test step is carried into
  the current workflow; all current-main steps are retained.
- Current-main analysis-index check passes. This package contains neither
  `REPORT.md`, `FORMAL_FAILURE.md`, nor `STOP.md`, so it is preparation material
  and is not counted as a retained result in the generated index.

## Execution boundary and status

The source `PLAN.md` requires one named, exclusive 20-minute CPU/container
window on a dedicated OrbStack VM with a private daemon and an already-cached
digest-pinned image. The checked #5085 coordination record contains a pending
request, not a named assignment or release. No OrbStack/Docker/WSLc container,
candidate CLI, auditor CLI, human, GUI, or model was invoked during recovery.
Formal candidate/auditor/retries remain 0/0/0. No fresh `FREEZE.json`, `run/`
receipt, or scientific result is claimed. The predecessor T0
`STOP_PREFORMAL_SCORER_GATE_MISSING` and its PR #6733 remain unchanged; this T0b
synthetic preparation is separate and does not satisfy the human time-on-task
hypothesis.

Issue #6503 remains open. Do not start the formal pair until the explicit
resource-owner assignment, private-daemon/image identity, fresh main/source/
output checks, and complete freeze are recorded. Construction CI is not that
authorization and is not a vigilance or product result.
