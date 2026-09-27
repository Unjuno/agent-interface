# Hedged evidence start v1 — Issue #4277

Allocation: `hedged-evidence-start-4277-20260923-01`

## H
After hard feasibility pruning, CHEAP-first scheduling with MEDIUM+EXPENSIVE hedged in parallel only after CHEAP returns AMBIG can remove the frozen sequential deadline misses while costing less than ALL_PARALLEL, without changing semantic decisions/YIELD.

## T
Deterministic standard-library event scheduler. Sources: CHEAP latency1 cost1, MEDIUM latency3 cost2, EXPENSIVE latency6 cost5. Nine frozen weighted cases compare SEQUENTIAL_VOI, HEDGED_AFTER_AMBIG, ALL_PARALLEL. Started-source cost is charged in full even if a result is later ignored. Infeasible sources are pruned before any policy starts them. No actual thread/process performance claim.

## D
PASS_HEDGED_EVIDENCE_START_SCOPED iff all policies match frozen semantic oracle/YIELD, infeasible starts=0, HEDGED has fewer deadline misses than SEQUENTIAL, no more misses than ALL_PARALLEL, lower weighted cost than ALL_PARALLEL, every late ignored result remains non-authoritative, independent audit errors=[], >=10 coherent evidence mutations reject, formal1/reruns0/replacements0/tuning0.

## C
Authored deterministic table; fixed full start cost ignores partial cancellation economics and shared provider resources. Costs/latencies may favor hedging.

## U
No real provider/model, actual parallelism, GUI/task, tokens, authority or product claim.
