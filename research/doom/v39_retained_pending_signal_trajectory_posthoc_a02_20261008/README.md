# V39 retained pending-signal trajectory, A02 guard replay

## H/T/D/C/U

**H.** In the retained V39 coast-liveness episode, the exact current-main typed health guard should preserve an admitted cover when health equals its authored hard minimum, and invalidate only after health falls below it. Replaying all observations in the three authored-policy windows should match the one invalidation recorded by the controller.

**T.** Reconstruct the six pending-model windows from frozen A01 inputs, then execute the exact `ObservableSignalGuard` source snapshot from current main `6ea1269defb6d48a607f13b08f1aa2d223ba06e9` over every paired health observation in the three authored-policy intervals. Verify report, event, delivered, A01 result, and guard source hashes. No game, model, controller, GUI, or OS input is started.

**D.** PASS if decision 1's health 85 at floor 85 and decision 5's health 51 at floor 51 classify as soft, decision 4 remains above its floor 55, and only decision 5 sequence 218 (health 48) is hard-invalidated, with no input authority granted. Any unknown, missing observation, source drift, or other hard event is FAIL/HOLD.

**C.** This is a posthoc rule-path replay of retained data, not a new live experiment. The source-to-terminal trace and exact guard semantics explain why equality did not interrupt; a liveness problem can still exist beyond the authored threshold.

**U.** The health reader is a HUD-template interpretation, not independent game-state truth. The replay does not demonstrate a fresh current-main controller schedule, better recovery, reduced damage, useful feedback, task completion, causal effect, or MAP01 exit.

## Result

The exact guard replayed 130 observations across the three authored windows with zero unknowns. Decision 1: 34/34 were `SOFT_CHANGED`, including seq62–70 at the floor 85. Decision 4: 44 observations were 28 `UNCHANGED` and 16 `SOFT_CHANGED`; the lowest health was 61, above floor 55. Decision 5: 51/52 were `SOFT_CHANGED`, including seq200–217 at floor 51; seq218 at health 48 was the only `HARD_INVALIDATED`. The historical controller report records one policy invalidation, consistent with the replay.

A01's inputs and outputs are copied unchanged so the closed README-only PR #8543 can be replaced by a complete, reproducible package. `GUARD_FREEZE.json` binds the new rule-path replay to the current-main guard blob and all prior A01 inputs.

## Reproduction

Use a new output directory on a volume with enough free space; the script refuses to overwrite an existing directory or any retained A01/A02 artifact:

```powershell
python -B verify_package.py
python -B run_package.py --out-dir D:\codex-research\v39-pending-trajectory-replay-output
```

This reconstructs the A01 result and audit, regenerates the guard replay, compares all three against retained outputs, and runs the unit tests under normal and optimized Python. The output directory receives only replay outputs and test logs.
