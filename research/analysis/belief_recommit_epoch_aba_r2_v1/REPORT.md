# #1872 Fresh belief recommit epoch ABA result

Decision: **PASS_BELIEF_RECOMMIT_EPOCH_ABA_SCOPED**

Every successful COMMIT/RECOMMIT in the candidate creates a fresh non-reused commit epoch. A prepared action receipt captures the commit epoch and the successful-commit count at preparation time. Action admission requires the receipt epoch to equal the current commit epoch in addition to ordinary fresh-support and contradiction checks.

## Exact weighted state result

Depth: 9 operations.

- trace-prefix nodes represented: 153,391,689
- transitions represented: 153,391,688
- candidate/oracle mismatch: 0
- successful commits: 1,523,288
- non-increasing successful commit epochs: 0
- archived old-commit witnesses: 27,332
- old prepared-receipt attempts after later recommit: 156
- candidate old-epoch ACTION admissions: 0
- candidate stale/contradicted ACTION admissions: 0
- fresh-current ACTION admissions: 60,522
- REUSED_COMMIT_ID comparator stale ABA admissions: 140

The discriminator is the ABA sequence: a receipt is prepared under an old commit, its support invalidates, the claim is freshly observed/validated and recommitted, then the old receipt is retried. With a fresh commit identity the receipt remains stale. When the comparator reuses the same opaque commit ID, some old receipts become equal to the new current ID and are admitted again.

Old commit records remain retained as historical provenance; the result requires identity freshness, not deletion of history.

Source-first canonical Git readback was 3/3 before formal. The independent tuple-state audit reconstructed every counter exactly. Formal invocation1; reruns/replacements/tuning0.

Scope: one claim and one commit stream. Production may use compound non-rebindable identities rather than integer epochs. No distributed commit, wrap/reuse, multi-claim atomicity, runtime performance, GUI/model/task/token/latency/product claim.
