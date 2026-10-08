# Fresh MAP01 exit-topology progress matched test

Decision: **REJECT_COVERAGE_AS_TASK_PROGRESS_PROXY / PASS_AUDIT**.

This is the fresh-seed successor to Issue #648 construction and Issue #652. The controller policy is byte-identical to the merged #595 normal-MAP01 bounded-deoptimization runner; only fresh seeds and the independently frozen scorer were added. No ATTACK input, model call, recovery-cover policy, automap, or controller-visible pose/sector information was introduced.

The scorer independently parsed the exact Freedoom MAP01 WAD (SHA-256 `a8772e088847032510d97ba2312406a6998f21cbab44d4ff10696faa9c0ecd4b`), found the unique ordinary exit linedef **774 / special 11** at `(184,-632)->(248,-632)`, resolved evaluator-only trajectory points through the BSP to sectors, and computed structural sector-hop distance to the two exit-adjacent sectors. This is a topology metric, not an exact dynamic-door shortest path.

Formal result across four matched fresh seeds:

| seed | baseline coverage | candidate coverage | coverage Δ | baseline min hops | candidate min hops | final hop Δ |
|---|---:|---:|---:|---:|---:|---:|
| 991500 | 23 | 29 | +6 | 15 | 15 | +2 |
| 991501 | 19 | 28 | +9 | 15 | 15 | -2 |
| 991502 | 20 | 29 | +9 | 15 | 15 | -2 |
| 991503 | 19 | 24 | +5 | 15 | 15 | +3 |

- candidate coverage non-worse: **4/4**;
- candidate strictly better minimum structural hops: **0/4**;
- paired median `(candidate min hops - baseline min hops)`: **0.0**;
- every arm reached minimum structural distance 15 hops; the candidate did not reach a deeper exit-topology state despite broader spatial coverage;
- candidate final health: 94, 94, 100, 81; all >= frozen floor 80;
- deaths and release failures: 0.

Euclidean minimum exit-segment distance was also identical at about 440 units in all eight runs. Final Euclidean distance often increased in candidate runs, but Euclidean distance is diagnostic only because walls/doors make straight-line proximity misleading. Final structural-hop direction was mixed (+2,-2,-2,+3 candidate-minus-baseline), so it does not rescue the primary minimum-progress claim.

Interpretation: the previously retained coverage benefit is real at its own metric but is **not evidence of additional exit-directed task progress** over this 45-decision horizon. Repeating longer coverage sweeps without adding task-relative guidance would therefore add little information. The next minimal mechanism should introduce a task-relative progress signal or planner-authored subgoal representation that can be checked from ordinary observations, while keeping hidden WAD pose/topology evaluator-only.

Limits: one map, four matched seeds, structural topology ignores current dynamic door/lift state, and no map exit occurred. This does not show the candidate is globally worse; it rejects coverage as a sufficient proxy for stage progress.
