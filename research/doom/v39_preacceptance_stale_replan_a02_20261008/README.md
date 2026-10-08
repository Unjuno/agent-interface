# Pre-acceptance stale-sequence recovery composition A02

This offline construction extends A01 to the exact current-main two-stage capture order. In the producer, sequence advances before it emits `typed_observation`; it emits the paired full image artifact afterward. An executor submit using sequence 1 can therefore be rejected before either sequence-2 event reaches the controller. A recovery must retain the typed row, wait for the full row, and match their sequence, capture time, pointer binding, and frame hash before opening a fresh planner turn.

## H / T / D / C / U

**H.** After the exact stale-sequence rejection, a bounded candidate can discard the old answer, retain the subsequent typed observation, wait for the matching full image using the existing controller wait function, and start a distinct planner turn whose prompt and image use that matched capture. It must not resubmit the rejected action. Non-stale rejection, missing either event, mismatched frame identity, or changed pointer binding must fail closed.

**T.** At current main `0c9bf746a8bb07564cde3d0c3283af6aff942be0`, AST-execute the exact `Backend.snapshot` method with inert image-capture, encoder/decoder, and artifact-publisher stubs plus a deterministic clock. Use the exact typed extractor, AST-extract production controller `wait` and `begin_model_turn`, and load the exact planner adapter. The resulting event schedule is stale rejection, typed sequence 2, then full sequence 2; both rows must share capture time, pointer binding, and RGB hash. Confirm the old planner answer is discarded and a distinct second turn receives health 86, ammo 12, and the matched image. Test non-stale rejection, no fresh observation, missing typed event, changed binding, and hash mismatch controls.

**D.** The candidate composition passes if the production wait ignores the typed-only event as a full image while the monitor retains it, the full row advances `latest`, all typed/full bindings and hashes match, the second planner turn includes fresh HUD and image, no input is resubmitted, and every negative control refuses.

**C.** PR #8492 establishes that current `execute_segment` raises on the pre-acceptance stale rejection. A01 tested recovery against a full observation arriving directly; A02 tests the actual typed-then-full event shape. This package still does not implement or execute a modified production controller.

**U.** Synthetic observations and planner responses only. No App Server, model, Doom process, GUI, OS input, live threat, cancellation, per-key release, useful task feedback, or game allocation ran. The PASS is candidate composition evidence, not current-runtime recovery or task-effect evidence; it does not close Issue #59.

## Result

`PASS_CANDIDATE_COMPOSITION`: the exact producer `Backend.snapshot` function ran with inert boundary stubs and emitted typed sequence 2 before its full image artifact. The controller wait consumed the typed row through a passive monitor, returned the matching full row, and advanced `latest`. The candidate verified capture, binding and RGB hash equality before deriving health 86/ammo 12 from the typed row. The exact `begin_model_turn` and planner adapter opened turn 2 with those values and the paired image. The old answer was not reused, no action was resubmitted, and all five fail-closed controls refused. The existing passive source-refresh helper still returned valid-but-stale sequence 1 as `already_observed` with zero submits.

This is distinct from #8478's hard-policy-invalidation path: that path cancels an already accepted active cover and transfers its matched full observation. Here the executor refuses a not-yet-accepted action before the delayed observation is delivered; no action cancellation or release wait is appropriate for that rejected ID. A live run must still establish whether this branch is useful under actual latency and preserves the end-to-end release and task-effect requirements.

## Reproduction

From the repository root, run:

```powershell
python research/doom/v39_preacceptance_stale_replan_a02_20261008/run.py
python -O research/doom/v39_preacceptance_stale_replan_a02_20261008/run.py
python research/doom/v39_preacceptance_stale_replan_a02_20261008/verify.py
```

`FREEZE.json` pins the main commit and Git blob identities. The scripts read production files from the checkout; they do not copy or edit them.

Two harness-development stops are retained in `DEVELOPMENT_FAILURE_01.txt` and `DEVELOPMENT_FAILURE_02.txt`: the partial checkout first lacked an imported source dependency; after that dependency was exposed, the source-refresh fixture lacked HUD values expected by its stub reader. These were setup/fixture defects before any composed result, not scientific outcomes. The final normal and optimized runs are preserved separately.
