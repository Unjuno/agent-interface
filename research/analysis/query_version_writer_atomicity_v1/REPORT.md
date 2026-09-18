# #1782 query-version writer atomicity

Decision: **PASS_QUERY_VERSION_WRITER_ATOMICITY_SCOPED**.

## Result

| publication protocol | unsafe acceptances | false invalidations |
|---|---:|---:|
| ATOMIC | 0 | 0 |
| MEMBERSHIP_FIRST | 2 | 0 |
| VERSION_FIRST | 0 | 2 |
| NO_VERSION | 2 | 0 |

Both insertion and removal directions are covered.

## Interpretation
The reader-side DYNAMIC_QUERY contract from #1773 is not sufficient by itself. Its scope membership version is trustworthy only if writers maintain membership and that version as one publication boundary.

Publishing membership first creates a window where membership is already different but the old query version still validates, so a stale query may commit. Never updating the query version leaves the same unsafe condition permanently.

Publishing the version first is safe in this primitive but causes a window where a reader rejects even though membership has not changed yet. Thus version-first can be conservative, while atomic publication gives the exact safe and non-overinvalidating contract.

## #165 ladder disposition
The four primitive rungs are now retained:
1. #1756 — control-predicate READ tracing;
2. #1767 — RESOLVE(alias, concrete_identity);
3. #1773 — QUERY membership version + current-member reads;
4. #1782 — writer-maintenance atomicity.

All four scoped formals PASS. This completes #165's requested primitive ladder without promoting a shared runtime implementation.

## Scope
No multi-writer transaction, durability/crash recovery, arbitrary runtime instrumentation, GUI, model, token, or production ABI claim.

## Next work
A separate integration issue should implement a bounded trace collector over one real execution substrate and measure whether it can produce these typed receipts without hidden bypass reads or excessive global invalidation.
