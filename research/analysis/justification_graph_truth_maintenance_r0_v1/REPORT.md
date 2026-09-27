# #1850 Incremental justification-graph truth maintenance result

Decision: **PASS_JUSTIFICATION_GRAPH_INCREMENTAL_TRUTH_MAINTENANCE_SCOPED**

Formal corpus: 5,000 deterministic acyclic justification graphs ×16 base masks ×4 single-base toggles =320,000 cases. Derived claims use OR-of-AND positive justification sets over earlier nodes.

## Exact result

- incremental/full validity-vector mismatch: 0
- changes outside reverse-reachable cone: 0
- blind descendant invalidation over-invalid cases: 73,878
- blind over-invalidated nodes: 147,149
- alternative-justification survival witnesses: 73,878
- direct-child-only bad cases: 49,916
- multi-hop invalidation witnesses: 49,916

Reverse-reachable incremental recomputation therefore matches a full fold exactly under the frozen complete-DAG assumptions. Blindly invalidating every descendant is safe but unnecessarily destructive when an independent justification remains satisfied. Recomputing only direct children is incomplete because changes can propagate through multiple derived levels.

The first construction attempt is retained in Issue #1850: only its hand-authored multi-hop negative-control fixture was wrong; the construction corpus already had mismatch0 and nontrivial discriminators. The directed fixture was repaired before source freeze/formal without changing the formal generator, seed or decision gates.

Independent audit regenerated the full corpus and matched every aggregate counter. Four corruption controls pass. Formal invocation1; reruns/replacements/tuning0.

Scope: finite acyclic monotone positive-support logic with complete dependency edges. No negation/defaults/probabilities/source trust/cycles/concurrency/action authority/runtime performance claim.
