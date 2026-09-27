# #4258 cost/selectivity predicate ordering v1

Decision: **PASS_COST_BASED_PREDICATE_ORDERING_SCOPED**.

One source/hash-frozen standard-library formal enumeration compared the authored `NAIVE_ORDER = D,C,B,A` with a development-only cost/selectivity order frozen as `A,B,C,D` for both AND and OR. Formal invocations/reruns/replacements/post-result tuning: **1/0/0/0**.

## Formal result

Both policies have:
- semantic wrong rate: **0**;
- UNKNOWN mismatch rate: **0**;
- p95 cost: **18**;
- p99 cost: **18**.

Frozen whole-decision weighted cost:
- NAIVE_ORDER: **16.61**;
- COST_SELECTIVITY_ORDER: **8.40**.

The optimized order therefore reduces the synthetic weighted predicate-cost endpoint by **8.21 / 49.43%** while preserving exact TRUE/FALSE/UNKNOWN semantics. Weighted predicate evaluations fall from **3.21 to 2.57** and p50 cost from **18 to 3**. The p95/p99 tails do not improve because expensive-required and unresolved-UNKNOWN cases still require all predicates.

The held-out shift block increases the importance of predicate B relative to development, but the frozen A,B,C,D order still preserves exact outcomes and the primary cost advantage. This is not evidence that the learned order is optimal under arbitrary drift.

## UNKNOWN semantics

The frozen three-valued contract is order-independent:
- AND short-circuits on FALSE even if an earlier predicate was UNKNOWN;
- OR short-circuits on TRUE even if an earlier predicate was UNKNOWN;
- if no decisive predicate appears and at least one UNKNOWN was observed, the final result is UNKNOWN.

The independent audit reconstructs this contract without importing `experiment.py`.

## Construction

One excluded construction invocation passed before freeze. It selected A,B,C,D for both expressions and produced diagnostic cost 8.40 vs 16.61 with zero semantic/UNKNOWN mismatch. No repair, second construction, threshold change, corpus change or tuning followed.

## Independent audit

Independent raw-only audit returns `PASS_COST_BASED_PREDICATE_ORDERING_SCOPED`, errors=[].

Eight copied-evidence corruptions were tested: decision, dropped row, weight, cost, used-order, truth, UNKNOWN laundering and policy removal. **8/8 rejected**.

## Scope

Finite synthetic sequential short-circuit evaluation only. Costs are deterministic units, not measured model/provider latency or tokens. Async/parallel predicate launch may dominate sequential ordering. No GUI/input/model/provider/network, task correctness, authority, safety or production-runtime claim follows.
