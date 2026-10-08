# Current-main V39 health-guard boundary during a pending planner — A01

## H / T / D / C / U

**H — Hypothesis.** With an authored V39 fire-cover policy based on health 100, critical floor 35, and maximum loss 12, the effective hard floor is 88. Health 89 and exactly 88 should preserve the existing cover; a fresh paired observation at 87 should invalidate it while the planner future is pending, cancel the cover before interrupting the planner, require a matching verified-empty terminal, and prevent an answer-eligible planner result from reaching Executor admission.

**T — Test.** Freeze exact current main `a6343bb76e4dc0a4afa32a29c8a485a617faeff8` and the transitive V39 source closure in `FREEZE.json`. The candidate extracts the exact production nested `wait()` and pending-future loop from `map01_overlap_controller_v39.py`, calls the production health/ammo monitor, `cancel_invalidated_cover()`, and final-admission function, and sends ordered typed observations 89, 88, 87 while a fake planner is waiting. It uses the pinned Codex Python runtime with network disabled.

**D — Decision.** A scoped pass requires 89 and 88 to remain soft changes, 87 to hard-invalidate at effective floor 88, Executor cancel to precede planner interrupt, verified-empty terminal release, and rejection of a deliberately answer-eligible planner answer without Executor admission or input authority. The independent auditor checks the frozen/current source identity and reconstructs these claims from raw JSON.

**C — Controls and scope.** This is a deterministic software-composition test with a synthetic typed health/ammo stream and a fake planner/terminal. `threat_present` is scenario metadata only. No Doom/game process, model provider, GUI, X server, operating-system input, container, or live allocation is used. It tests the current-main source snapshot, not physical key release or an application effect.

**U — Limits.** Passing establishes that the current V39 health guard can interrupt this pending-planner software path at its authored threshold. It does not show when the game first exposes an enemy, whether the live HUD sensor observes the change early enough, whether a physical release occurs per key, whether feedback is independently useful, whether bounded recovery helps, or whether the task survives or exits MAP01. A fresh, authorized current-main live threat exposure remains required.

## Reproduction

Run the frozen candidate once, then run the independent raw-only auditor and mutation tests:

```sh
/bin/bash run_once.sh
/Users/taka/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 audit.py results/candidate_raw.json
/Users/taka/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 -m unittest test_audit.py -v
```

The candidate command uses the fixed Codex Python runtime and macOS sandbox network denial. It writes one raw result. Do not rerun it after the retained one-shot; use a distinct allocation and path for any successor.
