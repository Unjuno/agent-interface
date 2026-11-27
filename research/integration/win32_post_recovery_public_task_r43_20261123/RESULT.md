# R43 result — current-main Win32 post-recovery task cohort

## Outcome

`PASS_SCOPED_FIVE_ATTEMPT_POST_RECOVERY_TASK_COHORT` on baseline `612b857d7c1c6a951d3f055862a5141dbc9c7637` (runtime tree `a8101de9d6bc868a523e412ec3a98d40d6a8649e`). All 5 frozen attempts passed, with 0 retries and 0 early stops.

For every attempt:

- The 2 s source authority expired; the public source action remained `UNKNOWN`, release-unconfirmed, `task_success: null`, and replay denied.
- The fixture independently recorded delayed `a` after expiry. The effect was not attributed as source task success.
- One public orphan recovery verified release, neutral readback, and the full 2 s late-input horizon.
- A distinct process/window/generation received one public `B` dispatch. The independent task oracle verified the `b` event within that dispatch execution interval; task success was true for this new task.
- Both fixtures closed after verified outcomes; the durable custody fence was clear after every attempt and at cohort end.

## Interpretation

This is a controlled, single-host Win32 fixture cohort on current main. It provides repeated evidence that a new public caller task can complete after recovery while preserving uncertainty and no-replay semantics for an earlier expired action. It is not a population reliability estimate, MAP01 or arbitrary-application validation, provider/model comparison, integrated efficiency result, Research Preview graduation, or distribution qualification.

The first independent audit invocation exposed a parser mismatch: verifier receipts are nested at `task_effect.receipt`. Raw outputs were preserved; `AUDIT-ADDENDUM-03.md` records the correction. Corrected evidence recomputation passes under normal and optimized Python. See `raw/trial-01` through `raw/trial-05`, `raw/cohort-summary.json`, and `FREEZE.json` for receipts and custody.
