# Partial-DAG recomputation proof

Let evidence leaves carry exact non-reused semantic version identities, and let every compute node be a deterministic pure function of its declared direct parents. The graph is acyclic.

## Sufficiency
For a compute node `v`, let `Dep(v)` be the transitive set of evidence leaves reachable backward through declared parents. If none of the changed evidence leaves is in `Dep(v)`, then every evidence value relevant to `v` is identical to the values used when its cached result was computed. By deterministic purity, every ancestor output relevant to `v` is also unchanged, so the cached output of `v` is identical to a fresh recomputation. Therefore `v` is safe to reuse.

## Necessity for universal safety
If some changed evidence leaf `e` lies in `Dep(v)`, choose one declared ancestry path from `e` to `v`. Define the compute function at every node on that path to project the path-parent value and let all off-path inputs be ignored. Change only `e`. The value propagates along the path and flips `v`. This is a valid family of deterministic pure node functions satisfying the declared graph. Therefore no generic scheduler can universally guarantee reuse of `v` once a transitive dependency version changes.

## Minimal recomputation frontier
A compute node is dirty exactly when it is forward reachable from a changed evidence leaf. Recomputing all and only these dirty compute nodes in topological order is safe: clean parents are reused and dirty parents are refreshed before their descendants. Any strict subset omits at least one dirty node and is not universally safe by the necessity construction. Any strict superset remains safe but performs avoidable recomputation.

The theorem fails if a node has undeclared hidden inputs, if version equality does not imply relevant evidence equality, or if nodes have nondeterministic/side-effectful semantics.
