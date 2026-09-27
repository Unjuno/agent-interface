# #1027 real adaptive-TTC eligibility audit v1

Final dependency-refresh snapshot main: `4b886e0cc79fb57ffce07b84b364eb886bde1cbf`.

Decision: **`HOLD_NO_REAL_ADAPTIVE_RESIDUAL`**.

This is the Rung0 eligibility result allowed by Issue #1027. It does not train, run or benchmark an adaptive policy. It asks only whether the repository currently contains a legitimate real `NEEDS_POLICY` residual with enough leakage-free residual rows and an independent semantic/effect oracle to justify the frozen `FULL_DEPTH` versus `ADAPTIVE_TTC` shadow experiment.

## Exact retained evidence

- Cross-domain rule VM result blob `20ed6bc4c682e5d2e1cf60fb44f4fcdf5a1bd21d`: Chromium exact 8192/8192; retained OpenTTD exact 5/5; fail-closed controls pass. Learned residual rows under those frozen contracts: **0**.
- MAP01 v31 last-effect result blob `9b131cc22860ca210959202790688a0759bc8b24`: five eligible retained rows, enriched collision groups 0. Its retained report explicitly says this does not establish population-level representation sufficiency and requires a materially larger leakage-free corpus plus an independent semantic/effect oracle before classifier/TTC activation.
- During this audit, upstream #1223 completed before publication. Its retained result blob `0b98bdfd7f00d063f252b5e9db27f9868eb4c9a8` is `PASS_PRIVATE_X11_OPERATION_TARGET_CONTRACT_SCOPED`: 12 fresh sessions / 96 rows, acceptable membership96/96, positive48/48, semantic negatives48/48, false executable0, stale executable0, missing arguments0, public/oracle leakage0, normalized incompatible groups0, independent audit PASS. The exact deterministic rule therefore closes this fresh real-state fixture too; learned residual rows: **0**.
- #1026 retained comment `5720862825` records `BLOCKED_REAL_SHADOW_DATA` rather than allocating a learner.
- #1027 retained update `5730673024` already states that the five-row v31 repair does not by itself activate adaptive TTC.

## Dependency refresh

The first local snapshot treated #1223 as an active upstream result and explicitly refused to consume it. Before PR creation, #1223 closed and its result appeared on main. The audit was therefore recomputed from the completed retained result instead of publishing stale dependency state. No #1223 experiment was rerun or changed. `DEPENDENCY_REFRESH.json` records this transition.

The new evidence strengthens rather than weakens the HOLD: a fresh 96-row private-X11 real-state census is fully closed by deterministic logic, so it cannot be reclassified as a learned `NEEDS_POLICY` residual merely to make adaptive TTC runnable.

## Six activation prerequisites

| prerequisite | current status |
|---|---|
| real caller-visible retained/shadow decision contract | yes |
| representation sufficiency for a **frozen learned residual** | **not established because no qualifying residual cohort exists** |
| genuine `NEEDS_POLICY` residual after deterministic coverage | **no** |
| enough leakage-free **residual** rows for frozen train/eval | **no; current qualifying residual rows = 0, while the separate MAP01 cohort is only 5 retained rows** |
| independent semantic decision/effect oracle | yes at the #1223 decision-level acceptable-set boundary |
| first transfer rung has no live-input authority | yes |

Three prerequisites therefore fail. The result is a dependency/eligibility HOLD, not a capability failure.

## Container validation

The refreshed source-bound validator reproduced the HOLD with no integrity errors. Five corruption controls were rejected as `FAIL_INTEGRITY`:

1. mutating the retained #1223 result blob identity;
2. declaring the five retained MAP01 rows sufficient against their source boundary;
3. relabeling deterministic-exact Chromium/OpenTTD rows as learned residuals;
4. relabeling the 96/96 deterministic-exact private-X11 rows as learned residuals;
5. using future/oracle evidence as a candidate feature.

The earlier precheck failure remains retained as scientific `NONE`: it attempted to manufacture a positive control by mutating retained source facts from five to 64 rows, and the exact-source validator correctly rejected that control fixture. The repair changed only control design, not H/T/D/C/U or source facts.

Independent audit does not import the validator and rechecks all three source result identities, deterministic closure, MAP01 five-row boundary, the three failed prerequisites and all five corruption outcomes.

## H/T/D/C/U result

**H:** current retained evidence is insufficient to activate adaptive TTC. **Supported at this refreshed snapshot.**

**T:** retained-source matrix + disposable-container validation only; adaptive formal invocations0; no training/model/GUI/X11/task input/provider call.

**D:** `HOLD_NO_REAL_ADAPTIVE_RESIDUAL`. Do not allocate `FULL_DEPTH` vs `ADAPTIVE_TTC` yet.

**C:** a later retained real desktop/task family may expose a genuine residual after deterministic coverage and provide enough independent rows. This HOLD must not be generalized into “adaptive computation is useless.”

**U:** snapshot-bound eligibility only. No classifier competence, adaptive speedup, safety, model-token, live-authority, or production claim.

## Next condition

Do not create a synthetic TTC substitute. Revisit only through a fresh successor after a completed retained real task family exposes a genuine `NEEDS_POLICY` residual not representable by the rule tier without semantic weakening and supplies enough leakage-free residual rows under an independent semantic/effect oracle.
