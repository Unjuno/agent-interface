# #1850 Incremental justification-graph truth maintenance R0

H: for finite acyclic monotone justification DAGs, recomputing exactly reverse-reachable descendants after one base toggle equals full recomputation; outside-cone nodes cannot change. Blind descendant invalidation over-invalidates with alternative supports; direct-child-only repair misses multi-hop effects.
T: seed-fixed corpus of 4 base +4 derived graphs with OR-of-AND justification sets, all16 base masks and4 single-base toggles; full vs incremental; two negative comparators; independent audit.
D: incremental/full mismatch0; outside-cone changes0; blind overinvalidations>0; direct-child-only bad cases>0; alternative survival and multihop witnesses>0; formal1/reruns0.
C: monotone positive acyclic complete dependencies only; no negation/default/probability/trust/cycles/concurrency/action authority.
U: analytical truth-maintenance prerequisite only; no runtime/model/task/latency/product claim.
