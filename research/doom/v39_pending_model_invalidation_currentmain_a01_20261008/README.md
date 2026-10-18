# Current-main V39 pending invalidation composition — A01

## H / T / D / C / U

**H — Hypothesis.** If a fresh paired health/ammo observation crosses the admitted health hard floor while the planner future is pending, the current V39 controller must cancel its active bounded cover before asking the planner transport to interrupt, accept only a matching verified-empty terminal receipt, and reject even a deliberately answer-eligible planner result before any Executor admission.

**T — Test.** Starting from current main `99f2521811df790db3c96cdfa9313a6296f247f7`, execute the exact production V39 nested `wait()` and pending-future loop by AST extraction. Use the production paired health/ammo monitor, `cancel_invalidated_cover()` and `final_admission_from_planner_result()`. Feed a fresh typed health value 80 against a frozen hard floor of 88 while a fake planner is waiting. The fake planner intentionally returns `answer_eligible=True` after the interrupt to stress the controller-level final gate. Its current `before_transport` hook records order; the matching executor terminal reports verified empty keys/buttons. Run once normally and once with Python `-O`.

**D — Decision.** `SCOPED PASS`: both runs passed 1/1. In both traces the order was Executor cancel then planner interrupt; the terminal was `cancelled` with verified-empty release; the model answer remained eligible in the fake but final admission was `REJECTED_POLICY_INVALIDATED`, with no Executor admission and no input authority. The independent raw audit passed all recorded checks.

**C — Controls and scope.** This is a deterministic, source-extracted local construction. The fake planner is intentionally more permissive than the production adapter to ensure the final gate rejects stale output independently. This does not run Codex App Server, a model provider, Doom/MAP01, GUI, OS input, or an actual key-release backend. The empty release is a fixture receipt, not physical release evidence. No formal allocation was invoked.

**U — Limits.** No useful task effect, threat response under real game time, physical per-key release, bounded live recovery, survival, or MAP01 outcome was measured. This does not close Issue #59.

## Reproduction

From repository root, with `research/live_control` on `PYTHONPATH`:

```powershell
$env:PYTHONPATH = 'research/live_control'
py -3 -m unittest research.doom.v39_pending_model_invalidation_currentmain_a01_20261008.test_pending_invalidation -v
py -3 -O -m unittest research.doom.v39_pending_model_invalidation_currentmain_a01_20261008.test_pending_invalidation -v
```

The raw traces, test logs, freeze manifest, audit, and checksums are stored beside this file. The production source tree is unchanged.
