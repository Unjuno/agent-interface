# Historical allocation recovery status

This record preserves the older ID001/ID002 preparation and failure history.
It is not a result for the target-belief hypothesis and is not a replacement
for the later ID003 allocation published in PR #4586.

## ID001 — `target-belief-admission-4150-20260923-01`

- The frozen source capsule is present in `target_belief_admission_v1/` and its
  XZ digest plus all nine declared member hashes were verified during recovery.
- The Issue records one attempted formal command, but Python stopped before
  loading study source. Scientific source started: 0; rows: 0/64; no result or
  audit was produced. Disposition remains `STOP_LOCAL_SOURCE_MATERIALIZATION`.
- The six excluded construction tests pass in the available offline Docker
  container. This does not execute or validate a formal allocation.

## ID002 — `target-belief-admission-4150-20260923-02`

- The branch retains its FREEZE, PLAN and source manifest only. Its declared
  6,228-byte source archive is absent from this branch; therefore the ID002
  source package is not complete or independently verified here.
- The Issue records `STOP_SOURCE_INTEGRITY`; preserve that disposition and do
  not infer any formal rows or result.

## Separation from ID003

ID003's distinct 64-row scoped contract result and its audit/control package
were published by PR #4586. This historical recovery does not alter, pool,
relabel or independently upgrade that result. No formal runner was invoked
during this recovery.
