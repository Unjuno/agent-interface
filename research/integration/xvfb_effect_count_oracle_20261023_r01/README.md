# Effect-count task-oracle repair — R01

The prior paused-Xvfb sample (PR #9424) recorded three old-window KeyPress/effect handlers while a repeated idempotent `[1]` property made the value-only task scorer pass. This repair adds a strict counted scorer to the current blocked-release fixture: exact `[1]` count before cancellation and at the horizon is required, alongside the original effect and all-up checks. Missing/malformed/non-CARDINAL evidence stays UNKNOWN. A fresh-task counter must transition `[0]→[1]→[1]`; later duplicates fail. Runtime UNKNOWN/no replay is unchanged.

The application now increments a separate non-idempotent X CARDINAL property for every handled task press on each old/fresh window. A separate parent X client reads the count before cancellation/input, after fresh input and at the horizon. The fresh readback interval includes both value and counter reads. These samples are sequential, not an atomic multi-property snapshot. They establish this fixture's handler/effect-count evidence, not arbitrary external exactly-once semantics.

The test now explicitly records `counted_task_outcomes`, separate from control-test completion. The other server-stop tests still use the legacy value/key-state scorers; their source docstrings now state that they do not establish effect multiplicity. No historical packet or result is rewritten, and no promoted runtime behavior is changed.

## Local verification

- `raw-red.txt`: five new tests initially fail because the counted APIs are missing (18 subtest/import errors); no native operation.
- `raw-final-normal.txt` and `raw-final-optimized.txt`: 20 pure oracle/signal-double tests pass in each mode. Cases reject repeated old effects despite unchanged values, late fresh duplicates, missing/invalid counts (including bool/negative/overflow), wrong effects and held input.
- `prior-raw-reconstruction.json`: separate offline diagnostic from the prior event trace changes the legacy value-only PASS to counted FAIL. Those derived counts are not new live counter observations and do not replace the prior result.
- The [new separately frozen live packet](../xvfb_counted_effect_local_20261023_r01/README.md) supplies the actual independent X counter reads: old count `[1]→[4]` correctly fails, fresh `[0]→[1]→[1]` passes. Its 24-check raw reconstruction and cleanup are retained separately.

Source freeze for live verification: `1c415fac6`; source identities and both local-command exit receipts are retained here. This fixes the measurement gap; it does not prevent repeated old held-key effects, establish their cause, undo the cancelled task, or solve MAP01, physical control, efficiency or reliability. The old task's FAIL and cancellation UNKNOWN are preserved.
