# A09 — native Xvfb V13 alias-cleanup successor

**Outcome: `STOP`.** This fresh candidate included the missing V10 dependency and reached the actual V13 executor. The owner refused the first key-down because the executor-created lease lacked the observed-focus field required by the owner (`ValueError: observed input focus required`). The terminal reports zero completed steps. Cleanup was verified empty and Xvfb exited 0, but the alias batch was not attempted. No retry occurred.

The raw-only audit v2 preserves this as STOP because the frozen alias refusal was not reached. See `results/A09_RAW.json` and `results/A09_AUDIT.json`.

A10 is a separately frozen fresh case that supplies the observed Xvfb focus to the lease. No production source changed; the alias guard remains candidate-only. No game/model/live MAP01 allocation was used.
