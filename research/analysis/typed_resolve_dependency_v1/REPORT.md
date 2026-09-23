# #1767 typed alias-resolution dependency

Decision: **PASS_TYPED_RESOLVE_DEPENDENCY_SCOPED**.

## Result
Across 16 prepared states and four single-resource mutations per state:

| policy | unsafe acceptances | false invalidations |
|---|---:|---:|
| DYNAMIC_RESOLVE | 0 | 0 |
| CONCRETE_ONLY | 16 | 0 |
| ALIAS_ONLY | 16 | 0 |
| STATIC_BOTH | 0 | 16 |
| GLOBAL_EPOCH | 0 | 32 |

Both alias targets A and B occur in 8 prepared states each.

## Interpretation
The dependency is genuinely typed. A prepared action depends on both the mapping that resolved an alias and the concrete object subsequently read. The concrete object's version alone cannot detect alias retargeting; the alias mapping alone cannot detect mutation of the selected object.

Tracking both possible targets is safe but over-invalidates mutation of the unselected target. A global epoch adds unrelated invalidation again.

## Scope
This establishes only a one-hop alias primitive with exact identity/version semantics. It does not cover collection membership queries, phantom insertion, multi-hop resolution, cycles, or atomic maintenance of query versions.

## Next rung
Follow #165 with `QUERY(scope, predicate_version)`: show that member-object reads alone miss insertion/removal phantoms and that a query/membership version is sufficient only when writers maintain it atomically with membership mutation.
