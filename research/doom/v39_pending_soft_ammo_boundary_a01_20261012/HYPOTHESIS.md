# Pending-turn soft ammo boundary A01

Date: 2026-10-12 JST. Exact source snapshot: current `main` `f185a9059d485a4f8d5a65e9e7f6782897f67eae`.

## H / T / D / C / U

**H — Hypothesis.** While a planner turn is pending, paired ammo evidence changing from 6 to 4 is above the current cover monitor's hard floor of 1 but below a next-action minimum of 5. The monitor records this as a soft event without emitting a policy invalidation, so the pending-turn cancellation path does not run. At ammo 0, the hard boundary emits invalidation and reaches the controller's cancellation branch.

**T — Test.** Extract the paired health/ammo monitor functions from the frozen current-main controller and execute two coherent typed observations (6→4, 6→0). Inspect the exact main pending-turn loop to verify it observes through this monitor and only calls `cancel_invalidated_cover` for `policy_invalidation`. Run the replay in normal and optimized CPython, then independently audit source identities and decisions.

**D — Decision.** Pass if all eight runner checks hold in both modes and the independent audit passes every source, output, and predicate check. A fail or mismatch stops this construction result; it does not authorize a live retry.

**C — Competing explanation.** `minimum_ammo=5` may constrain only the next model-authored action, while the already-admitted cover may intentionally remain valid down to 1. This synthetic result does not show that a live cover includes repeated fire, that firing below 5 is unsafe, or that the monitor is defective.

**U — Uncertainty.** Synthetic HUD values and control-flow inspection only. No running game, live app-server/model turn, OS input, physical release, feedback usefulness, survival, or task effect was measured. The live experiment must record the active cover commands and ammo crossing while the planner is actually pending.

## Result

Both cases passed. At ammo 4, the monitor returned no invalidation and recorded one soft event; the pending-turn cancel condition remained false. At ammo 0, the monitor returned `ammo:below_hard_minimum`, matching the controller cancellation branch. The independent audit is 14/14. This narrows the live question: does an already-running cover keep issuing fire after ammo falls below its authored next-action floor, and is that behavior useful or harmful under threat?

This does not close Issue #59 or establish that the observed contract is a bug.
