# Result — persistent epoch retirement and exclusion GC (#4344)

**PASS_EPOCH_RETIREMENT_ORDER_SCOPED**. Public source/gate freeze commit `cf284f2dc0f8c5d805c072177b32c83aa74ea8b2` preceded all formal cases. All nine source-surface Git blobs matched local bytes before authorization comment5825575544. Six four-case batches executed once; no rerun, replacement, exclusion or tuning.

| Endpoint, per12 cases | DELETE_FIRST | FENCE_FIRST |
|---|---:|---:|
| Previously excluded old request becomes eligible |4|0|
| New epoch request eligible after durable installation |2|6|
| Completed maintenance acknowledgements |2|2|
| Retained exclusion rows, summed over12 separate DBs |18|30|

The discrepancy occurs only after the first commit and before the second. With deletion first, both BETWEEN_COMMITS and SECOND_UNCOMMITTED reopen epoch7 with empty exclusions, so(7,A) becomes eligible. With fence first, those same cuts reopen epoch8 with3 obsolete rows retained. Old epoch requests are rejected and fresh(8,A) is eligible. Both completed-maintenance controls reach epoch8 with no old rows. Baseline, first-uncommitted and wrong-expectation controls preserve epoch7/three exclusions. Future epoch9 is rejected in all24 cases.

## Interpretation and negative evidence

Persistence of each individual transaction is not sufficient: the two-transaction order must preserve the rejection invariant at intermediate persisted states. An atomic combined transaction is an alternative but was not tested and is not required by the proved two-step contract.

Fence-first can leave obsolete records after interruption; its12 extra retained rows are four separate intermediate databases with3 rows each, not a cumulative storage benchmark. Logical deletion does not show disk-space reclamation. Switching epoch also rejects previously unseen old-epoch work. Eligibility is only a read-only proposal decision: no payload, input or task effect is executed and every result has authority_granted=false/task_success=null.

## Complete execution and audit

24 cases,96 read-only probe outcomes,48 scientific child processes:12 deliberately abrupt exit23 and36 natural exit0. Six case-batch processes and six outer supervisors exit0. No timeout. Main audit475 checks/errors=[], all12 effective well-formed copied-evidence controls rejected, eight unit methods passed before freeze. Construction12 cases/24 children is separate, with its233-check audit and12 effective controls retained. Same-author separate code/process auditing is not independent human review.

The first shell audit JSON/stderr are retained. Its PID/exit was not separately captured; a subsequent explicitly read-only invocation recorded its own exit0 and reproduced the first JSON byte-for-byte. No missing first-auditor status is inferred and no scientific actor was rerun. Actual scientific actors and batch waits are fully recorded.

## Environment and applicability

Provided Linux x86_64 container, CPython3.13.5, SQLite3.46.1, DELETE journal, synchronous FULL, explicit BEGIN IMMEDIATE/COMMIT, timeout0. CPU affinity0..4, frequency unpinned; no timing endpoint. Docker/gh not available; no Docker/OrbStack image identity. Abrupt process exit is not a power failure. Initial, before-reopen and after-reopen DB/journal bytes are included in each case, not only their hashes. SQL completion markers follow actual successful commits. Auditor opens reconstructed copies to check SQLite state/integrity without changing originals.

Trusted monotone epoch installation, one owner, no concurrent admission/maintenance, same durable DB and no in-flight body grants are assumptions. No authentication, rollback/loss, split brain, transport cancellation, model/token/latency/task benefit or production claim. See PLAN.md for full H/T/D/C/U, variable/unit table, conditional proof and all cuts.

## Preservation and integration

Closed #544/#531/#24 and active #4037/#4332/#4335 remain unchanged. The ra91 and b83 conversation studies were not rerun or imported; prior blocked publication sources are not part of this work. Only the owned additive research directory changes. This evidence informs #24/#2789 recovery: commit a namespace-level exclusion mechanism before deleting per-request exclusions. It does not close the repository-wide ROADMAP or promote a runtime.
