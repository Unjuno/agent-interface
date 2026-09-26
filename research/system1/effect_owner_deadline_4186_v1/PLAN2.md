# Issue #4195 allocation ID002 delta plan

Allocation: `effect-owner-deadline-4195-20260923-02`.

ID001 is immutable `STOP_EXTERNAL_EXECUTION_TIMEOUT / HOLD_FORMAL_INCOMPLETE` with20 complete rows, one partial case directory and15 unstarted rows. ID001 rows are not pooled or reused.

## Scientific H/T/D/C/U
Unchanged from the public Issue and PLAN.md. Policies, schedules, task deadline120ms, freshness400ms, app/sink source, effect-file contract, oracle and acceptance gates are byte-identical.

## Only delta: orchestration granularity
Instead of one 36-row process under a 45-second outer envelope, ID002 uses three immutable 12-row batches, one repetition per batch. Each batch is invoked once into a new directory and writes its own END.json. The surrounding shell records an external exit file. Batch N+1 may run only after batch N has END rows12/exit0 and external exit0.

Frozen commands:
- `python -B batch.py --out formal2/batch-0 --rep 0`
- `python -B batch.py --out formal2/batch-1 --rep 1`
- `python -B batch.py --out formal2/batch-2 --rep 2`
- `python -B audit_batches.py formal2 --out AUDIT2.json`
- `python -B controls_batches.py`

No case replacement, pooling, threshold/source change or favorable retry. Missing/nonzero batch stops ID002 and preserves the prefix.
