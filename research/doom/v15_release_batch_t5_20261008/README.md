# V15 release-batch mixed-schema fail-closed T5

This successor tests a telemetry-integrity gap in the T4 adapter prototype. Current-main V15 emits `release_batch_delivery_position` for rows in a program-wide delivery stream. T4 also accepted the older row contract with no such field. If one row in a program stream had the field and another lost it, T4 split the rows between new-stream and legacy validation. A two-release synthetic trace then passed as `TEMPORALLY_UNIQUE` despite the incomplete delivery ledger.

T5 added a fail-closed rule: a program/batch identifier cannot mix legacy rows with current delivery-position rows. The identical source-shaped fixture changes from `SOURCE_ROWS_JOINED / TEMPORALLY_UNIQUE` under T4 to `HOLD_INCOMPLETE_RELEASE_BATCH / UNRESOLVED` under T5. The old result does not establish causality; both results retain `NOT_ESTABLISHED`.

## Verification

- RED: new test failed on the T4 prototype with the false `SOURCE_ROWS_JOINED` result.
- GREEN: 28/28 tests pass normally and 28/28 under `python -O`. These include the previous V15 adapter/T0 suite plus six delivery-batch tests.
- Independent raw-output audit: `PASS_MIXED_SCHEMA_FAIL_CLOSED_SCOPED`.
- The freeze pins current main `2a9052efdd155b8cdc173d216a969ea5f64a1ce9` and the exact unchanged backend blob `193c2bd231795e7ee57de64aedfd741c8b814013`.

This is synthetic adapter construction, not evidence of runtime reliability. No GUI, OS input, game, model, real scorer, live allocation, task effect, useful feedback, recovery, safety, speed or completion was tested. Current project direction r139 still prioritizes a fresh live threat exposure; Issue #59 and the game lane remain unassigned. The package lives on D: because C: has zero free space; the repository worktree was not changed. See `FREEZE.json`, `RESULT.json`, and `AUDIT.json` for provenance and the scoped audit.
