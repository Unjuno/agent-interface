# #1756 typed dynamic branch read-set

Decision: **PASS_TYPED_DYNAMIC_BRANCH_READSET_SCOPED**.

## Result
Across all 16 binary prepared states and four single-resource mutations per state:

| policy | unsafe acceptances | false invalidations |
|---|---:|---:|
| DYNAMIC_TYPED | 0 | 0 |
| DATA_ONLY | 16 | 0 |
| FULL_STATIC | 0 | 16 |
| GLOBAL_EPOCH | 0 | 32 |

The dynamic tracer records exactly the path-specific set `{g, executed_branch_resource}` in all 16 states. Both branch directions occur 8 times.

## Interpretation
The control predicate is a real dependency even when a particular value coincidence would make a stale branch happen to produce the same output. Omitting `g` therefore fails structurally, not merely statistically.

Conversely, tracing the unexecuted branch is safe but unnecessarily invalidating, and a global epoch adds another unrelated invalidation source. For this primitive, typed dynamic tracing reaches the safe/non-overinvalidating point that static or global strategies miss.

## Scope
This is only one deterministic branch. It does not establish alias resolution, collection/query phantom handling, writer-maintenance atomicity, automatic tracing across arbitrary runtimes, or production ABI semantics.

## Next rung
Follow #165's ladder with `RESOLVE(alias, concrete_identity)`: trace both the alias-resolution dependency and the resolved object dependency, then distinguish retargeting of the alias from mutation of the concrete target.
