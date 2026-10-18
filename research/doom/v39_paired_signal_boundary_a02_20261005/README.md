# V39 paired-signal fail-closed outcome A02

## H/T/D/C/U
- **H:** The V39 pair monitor's invalidations return a complete fail-closed outcome: new decision required, no input authority granted, only preservation/reduction of existing authority, and no task-success assertion.
- **T:** Execute exact AST-selected helper/class definitions from the source-bound controller with stub reader/guard interfaces; capture full invalidation receipts for nine frozen valid/fault cases. Independently audit every response field and reject five output mutations.
- **D:** PASS only if all nine expected observations match, all invalidation outcome fields have the frozen fail-closed values, the independent audit passes, and every authority/success mutation is rejected.
- **C:** Guard and reader interfaces are stubbed; extraction does not exercise producer timing, runtime integration, or actual frame capture.
- **U:** Synthetic construction only. No live game, planner, physical input, useful feedback, recovery, latency, or task outcome.

## Relation to A01
A01 remains unchanged. This is additive successor A02, created after review found that A01 retained reason strings but not the invalidation outcome. A02 preserves complete response fields so both candidate and independent audit check authority semantics.

## Run
One WSLc candidate run, network disabled, configured 1 CPU / 512 MiB, cached `python:3.12-slim`. Raw candidate output: `raw.json`. The independent audit includes five in-memory output mutations; it does not rerun the candidate or mutate the source.
