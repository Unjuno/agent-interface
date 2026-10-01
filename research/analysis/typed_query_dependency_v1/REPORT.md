# #1773 typed query dependency

Decision: **PASS_TYPED_QUERY_DEPENDENCY_SCOPED**.

## Result
Across 32 prepared collection states and five single-resource mutations per state:

| policy | unsafe acceptances | false invalidations |
|---|---:|---:|
| DYNAMIC_QUERY | 0 | 0 |
| MEMBER_ONLY | 64 | 0 |
| QUERY_ONLY | 32 | 0 |
| STATIC_SCOPE | 0 | 32 |
| GLOBAL_EPOCH | 0 | 64 |

Membership shapes cover empty 8, partial 16, full 8 prepared states.

## Interpretation
Current-member reads are insufficient because insertion/removal can change the query result without changing any already-read member. A scope membership/query version closes that phantom class.

The query version alone is also insufficient because the values of currently present members can change while membership remains stable. The minimal typed trace for this primitive is therefore the query membership version plus the value/version reads of current members.

Static tracking of absent members is safe but over-invalidating; a global epoch adds unrelated invalidation.

## Scope
This result assumes writers maintain the scope query version correctly. It does not prove atomic coupling between membership mutation and query-version update.

## Next rung
The final #165 primitive rung is writer-maintenance atomicity: deliberately separate membership mutation from query-version increment and prove there is an unsafe window even though the reader uses the correct DYNAMIC_QUERY trace.
