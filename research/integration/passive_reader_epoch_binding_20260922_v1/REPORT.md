# Producer-lifetime binding: first formal result

**PASS_PRODUCER_EPOCH_BOUNDARY_SCOPED** — Issue #3933.
One predeclared 48-case allocation; no formal rerun or replacement.
This is research-only evidence, not runtime/GUI/model integration or production promotion.

## Result

| Directed scenario | Legacy (three repetitions) | In-band epoch (three repetitions) |
|---|---|---|
| Same producer appends | 3 correct resumptions | 3 correct resumptions |
| Reader restarts, same lifetime | 3 correct resumptions | 3 correct resumptions |
| Producer restarts, identical logical records | 3 cross-lifetime aliases | 3 prefix refusals |
| Producer restarts, same consumed prefix | 3 cross-lifetime aliases | 3 prefix refusals |
| Producer restarts, changed consumed prefix | 3 prefix refusals | 3 prefix refusals |
| Producer restarts, shorter file | 3 prefix refusals | 3 prefix refusals |
| Old prefix plus new-lifetime suffix | 3 cross-lifetime aliases | 3 epoch refusals |
| Explicit fresh epoch and no old cursor | 3 correct adoptions | 3 correct adoptions |

The legacy misuse remains rejected: reusing a saved stream ID/cursor across
producer lifetimes was already outside HOST_CONTRACT.md. The experiment
supplies actual finite process/file counterexamples and a scoped candidate,
not discovery of an undocumented upstream guarantee violation.

The candidate's fifteen stale-lifetime cases expose neither a record list nor
a new cursor. Normal append, reader restart and explicit new-epoch adoption
succeed in all eighteen positive cases across both protocols. In particular,
the mixed-prefix case shows why checking each returned record matters: an
unchanged consumed-prefix digest alone cannot identify the appended lifetime.
An ordinary changed/shortened prefix is still rejected by the exact old reader.

## Independent checks and provenance

The supplied Linux x86_64 container executed 84 producer processes and 96 reader
processes. Each producer used the exact retained DeliveryLedger.prepare;
readers used the exact retained read_pending. Candidate changes only the
persisted per-record field and an all-or-nothing exposure check. All 180 child
exit codes were integer zero; all returned authority/ACK/input flags were neutral.
No model/provider, network experiment, GUI/input or production service was used.

A separate process running audit.py imports no runner, candidate, ledger or
reader. It reconstructs the schedule, exact record bytes, producer commands,
epoch/PID identity, read requests/responses, prefix hashes, cursors and exit
receipts from retained raw data. Its first formal audit passed with errors [].
It is independently implemented checking within the same environment and by
the same author, not an independent external reviewer or a second engine.

All eight evidence corruptions were rejected: missing case, duplicate case,
wrong producer epoch, modified payload with recomputed snapshot digest, invented
input dispatch, missing exit receipt, boolean exit code, and changed cursor hash.
Eight unittest methods passed (six gate checks plus baseline and mutation group).
The candidate's empty-read test does not infer producer termination or ACK.

| Artifact | SHA-256 |
|---|---|
| Preformal FREEZE.json | 33a7ae8a374eb3e2db1fe2ad49ec9b887905a2a350f2e8f3d9fb463054173a9e |
| Formal RAW.json | 103bf32ca14d060edc80f18c52caf337c4b0d69cdcc9e86bc99e6249305349c2 |
| First formal audit stdout | 483892d358008c186535b38d2f7cf07d2361096c78082629814c088937ea4d7e |
| Complete packed evidence payload | 7a38bbe3f094c45973f46ae5f01ed5691622ffe7b550429de5895ed3cc60592e |

The source hash declaration was posted in #3933 comment 5766217967 while formal
invocations were zero. First-result comment 5766251983 records the outcome.
The runner verifies sources before and after execution. Source Git delivery
readback found ENVIRONMENT.json missing only its terminal LF in the first
publication commit; publication restores the exact frozen 371 bytes rather
than altering the executed source or FREEZE.json. All other frozen blobs matched.

## Failures and exclusions retained

Construction-01 was stopped by its 45-second outer tool limit after fourteen
complete case records and a partial fifteenth. No terminal exit receipt survived;
it is STOP_OUTER_TIMEOUT, not a PASS. Construction-02 completed sixteen excluded
cells under a bounded supervisor. A construction-label-only audit correction and
addition of control-result retention preceded the formal freeze. Both initial
and corrected audit results and the first four source preimages are preserved.
No construction case contributes to the formal denominator; see CONSTRUCTION.md.

## Scope and integration handoff

This study owns only per-record epoch binding under ordered finite lifecycle
transitions. Parallel #3931 owns crash persistence; #3937 descriptor rotation;
#3938 immutable-generation path lookup; #3941 concurrent cursor commits;
#3947 input file-kind admission; #3952 partial UTF-8 tails; #3917 live producer
integration. No shared code, those paths, or old evidence was changed.

Owner-selected unique/persisted epochs are assumed, not inferred or authenticated.
The private fixtures are not a production epoch allocator or producer contract.
Empty files, epoch reuse, hostile producers, in-place writes during one read,
concurrent namespace lookup, multiple producers, power-loss durability, ACK,
model viewing, exactly-once delivery, current action authority and performance
are not established. An old-but-consistent notification is not current-state
permission to act. Full #3876 and the repository ROADMAP remain open.

The finite roadmap is source reconstruction, construction, freeze, formal48,
raw audit/controls and an additive evidence PR. Integration should compose
validated contracts only after actual producer/host ownership and lifecycle
are specified. Do not promote this fixture or invent a generic background queue.
