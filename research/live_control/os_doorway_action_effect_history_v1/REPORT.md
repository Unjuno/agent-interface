# OS-screen doorway action-effect history under pixel aliasing

Task `OS-DOORWAY-ACTION-EFFECT-HISTORY-20260916-001`, Issue #459.

## Decision

**`PASS_OS_DOORWAY_HISTORY_SCOPED`** for completed allocation `os-doorway-history-20260916-a2`.

The first allocation `a1` is separately retained as **`INCOMPLETE_SUPERVISION_TIMEOUT`** after 18/24 cases and is not pooled into `a2`.

## Question

Can one predecessor OS-screen observation provide task-relevant information when the decision-time current screen is byte-identical across two states, and can that information improve a real OS-input effect rather than only an offline classifier?

The synthetic doorway has two hidden trajectories. Both reach the exact same decision-time current pixels. Opening should continue with `Right`; closing should continue with `Left`. The baseline receives only the current frame and uses frozen deterministic `Right`. The candidate receives predecessor plus current and uses the signed door-panel displacement. Both emit exactly one XTEST key press/release, and the application writes an independent terminal effect receipt.

## Retained allocation history

### A1 — retained partial

A1 used the source-first frozen scientific design but one monolithic 24-case outer invocation. The external container supervisor terminated it at 60 seconds after 18 complete first cases. No child process remained. Completed prefix: history 9/9 correct, current-only 4/9 correct, one exact current RGB hash, input empty 18/18. Cases m19..m24 never started. A1 was not resumed and contributes zero rows to the A2 score.

### A2 — completed successor

A2 changes only outer supervision: the same 24-row trajectory/policy order is executed as four six-case invocations using fresh IDs n01..n24. App source, per-case measurement source, auditor, environment, scientific gates and effect semantics are unchanged. A preformal GitHub readback found an indentation-only remote transfer mismatch in `run_chunk_a2.py`; it was repaired to the already-declared local bytes before any A2 case ran. Final remote Git blob equals local `git hash-object`.

## First outcomes

| Policy / trajectory | Correct | Total |
|---|---:|---:|
| history / opening | 6 | 6 |
| history / closing | 6 | 6 |
| current-only / opening | 6 | 6 |
| current-only / closing | 0 | 6 |

Aggregate: history **12/12**; current-only **6/12**.

All 24 decision-time current RGB observations have the same SHA-256:

`32a172e095016952eeb3ff83d69aa5f196b23216b56b40d55d7d8238ed9faa95`

The predecessor images differ by motion direction. The independent auditor reconstructs the door-panel centroid from retained PNG pixels, checks opening predecessor < current and closing predecessor > current, checks controller decision against the frozen policy, checks the application effect receipt against that decision and expected trajectory, and verifies final key release.

Input state is empty in **24/24** completed A2 cases. Audit errors: **0**.

## Integrity

Frozen audit output SHA-256: `c42138369cbf1131b2223a205115c4a01f58281d72647397d9c7e9762ad0cce3`.

Five postformal controls were applied only to copied evidence/source. The auditor rejected all 5/5: result image-hash claim, task-correctness claim, release claim, executable source bytes, and schedule identity.

No A2 measured ID was rerun or replaced.

## Interpretation

This result crosses the narrow boundary left by PR #445: temporal/action-effect information can improve an **actual OS-input task effect** in a case where the current OS-screen observation is provably identical and insufficient for the balanced task. The effect is not inferred from the controller decision; the Tk application separately records which key it received and whether that key is correct for the hidden trajectory.

The result does **not** establish that MAP01 naturally presents this alias at a useful frequency, that one-step history is generally sufficient, or that a planner/model can choose or use the history representation correctly. It also does not establish speed, reliability rates, long-horizon navigation, threat survival, or a shared-runtime promotion.

## H / T / D / C / U

**H:** one predecessor frame resolves the authored opening/closing alias and should give 12/12 history correctness versus exactly 6/12 for a fixed current-only policy on the balanced matrix.

**T:** 24 fresh A2 cases, two trajectories, two policies, private Xvfb/Tk process per case, XGetImage screenshots, one XTEST Left/Right effect, independent application receipt, source-first freeze, no model/game/network call.

**D:** PASS only at history 12/12, current-only 6/12, one exact current RGB identity, effect/action consistency, input empty 24/24 and independent audit PASS. All gates passed.

**C:** the fixture deliberately authors the alias, and the current-only baseline is deliberately deterministic rather than an optimized stochastic classifier. The benefit could therefore be large because the experimental task is constructed to isolate the information difference.

**U:** synthetic Tk doorway, Xvfb/XTEST, two discrete trajectories, no ViZDoom or natural alias-rate estimate. A later real-domain transfer must first independently establish current-observation insufficiency rather than assuming it.

## Next single question

Use the same bounded-history principle on one real-domain OS-screen/OS-input transition where the current observation is independently shown insufficient for the task effect. Do not jump directly to another full MAP01 objective run and do not add model inference in the same rung.

## ERROR CHECK

The completed A2 denominator is 24 and excludes all 18 A1 partial rows. Every A2 case appears exactly once in the frozen schedule and exactly once in retained result evidence. The reported 12/12 and 6/12 totals agree with the four 6-case strata above. No current-screen difference is available to explain the policy difference because all current RGB bytes share one SHA-256.
