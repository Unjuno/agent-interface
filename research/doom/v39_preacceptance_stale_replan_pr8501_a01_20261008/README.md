# Pre-acceptance stale-sequence recovery composition A01

This offline construction asks whether the existing current-main observation wait and planner-input functions can support a bounded fresh replan after an executor rejects a segment before acceptance. It builds on PR #8492's reproduced schedule: the producer advances to sequence 2 before delivering its full observation, so an action submitted from sequence 1 is rejected first.

## H / T / D / C / U

**H.** After the exact stale-sequence rejection, a controller can discard the old answer, wait for a strictly newer full observation using the existing controller wait function, and start a distinct planner turn whose prompt and image use that observation, without resubmitting the rejected action. A non-stale rejection, missing fresh observation, or changed pointer binding must fail closed.

**T.** At current main `3d5f91f4409a79eabb332187d7ad2639ec8106c9`, AST-extract the production nested `wait` and `begin_model_turn` functions and load the exact `PersistentPlannerAdapter`. First pass a stale-but-HUD-valid sequence-1 source through the exact signal-unknown refresh helper; then feed a rejection for expected sequence 1 followed by a full observation at sequence 2 (health 86, ammo 12, same pointer binding, distinct image). The first fake planner result is marked stale by the candidate harness and discarded; the second turn must carry sequence-2 HUD values and image. Exercise controls for a different rejection reason, no fresh observation, and changed pointer binding.

**D.** The candidate composition passes if the source wait advances `latest` to sequence 2, the second adapter turn includes sequence-2 HUD and image, no input is resubmitted, and each negative control refuses without another planner turn.

**C.** PR #8492 already establishes that current `execute_segment` raises on the pre-acceptance stale rejection. This package does not implement or execute a modified production controller. It tests whether selected existing source functions can support a recovery candidate after that rejection.

**U.** Synthetic observations and planner responses only. No App Server, model, Doom process, GUI, OS input, live threat, cancellation, per-key release, useful task feedback, or game allocation ran. The PASS is candidate composition evidence, not current-runtime recovery or task-effect evidence; it does not close Issue #59.

## Result

`PASS_CANDIDATE_COMPOSITION`: the existing passive source-refresh helper returned valid-but-stale sequence 1 as `already_observed` with zero submits. The exact current-main wait then consumed the newer full observation after the stale-rejection event and updated `latest`. The exact controller `begin_model_turn` function and planner adapter opened turn 2 with health 86, ammo 12, and the sequence-2 image. The turn-1 answer was not reused and no new input submit occurred. All three fail-closed controls refused.

This is distinct from #8478's hard-policy-invalidation path: that path cancels an already accepted active cover and transfers its matched full observation. Here the executor refuses a not-yet-accepted action before the delayed observation is delivered; no action cancellation or release wait is appropriate for that rejected ID. A live run must still establish whether this branch is useful under actual latency and preserves the end-to-end release and task-effect requirements.

## Reproduction

From the repository root, run:

```powershell
python research/doom/v39_preacceptance_stale_replan_a01_20261008/run.py
python -O research/doom/v39_preacceptance_stale_replan_a01_20261008/run.py
python research/doom/v39_preacceptance_stale_replan_a01_20261008/verify.py
```

`FREEZE.json` pins the main commit and Git blob identities. The scripts read production files from the checkout; they do not copy or edit them.
