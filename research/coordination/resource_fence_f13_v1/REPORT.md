# Resource-installed epoch fencing — Issue #4349

**PASS_RESOURCE_FENCE_BOUNDARY_SCOPED**. This is one new, publicly source-frozen, directed engineering allocation, not a production result or a new fencing algorithm. Preserve #4344/#544/#24/#628 and all other evidence unchanged.

## First outcome

36 cases, 72 resource APPLY requests, six immutable six-case batches, each once. No case rerun, replacement, exclusion, or post-freeze source tuning. The first independent raw DB/IPC audit ran 2,438 checks with errors=[]; all 12 effective, well-formed copied-record mutations rejected through ordinary audit errors, not parser crashes. The first audit and control process PID/exit receipts are retained.

| Per 12 cases | ISSUER_ONLY | MAX_SEEN | INSTALLED_EPOCH |
|---|---:|---:|---:|
| Resource APPLY requests |24|24|24|
| Applied private DB effects |24|20|12|
| Old effects after issuer retirement |12|8|2|
| Fresh epoch8 effects |10|10|8|
| Fresh epoch8 refusals |0|0|2|
| Additional resource INSTALL RPC pairs |0|0|10|

The candidate's two old effects occur BEFORE its resource installation in DELAYED_FENCE. It has zero old effects AFTER the resource installation commit. The post-installation metric for the other modes is inapplicable, not an additional zero-violation success: they have no INSTALL operation. Their zero-valued generic audit field is therefore not used for comparison.

A highest previously accepted token is a legitimate weaker contract: NEW_FIRST advances MAX_SEEN to8 before old7 arrives, so old7 is rejected. IDLE_RETIRE and RESOURCE_RESTART leave its high-water at7 despite issuer retirement to8; old7 is accepted. Only the explicit mode installs8 before this old request arrives. This costs 10 extra request/response pairs across its12 cases. In PREINSTALL_NEW, that mode intentionally refuses a fresh8 request arriving before resource installation, then accepts a DISTINCT fresh8 request after installation. No refused request is retried.

## Concrete counterexample and positive limitation

Issuer and resource start at7. The issuer creates old-A/old-B, then commits retirement to8. The resource has its own DB; it cannot infer this change. An old-A request at7 therefore satisfies e>=h when h=7 under MAX_SEEN. If resource INSTALL commits r=8 first, e=7 fails equality e=r. After a fresh request at8 has already applied, MAX_SEEN h=8 also rejects7. These are different information/coordination boundaries, not evidence that all token fencing is defective.

In DELAYED_FENCE the old-A effect commits before INSTALL even in the candidate. The later fence cannot undo that effect. Retaining both that effect and the early-new refusal is essential; neither is hidden to claim immediate issuer-side revocation.

## H/T/D/C/U and proof

See the exact frozen source/PLAN.md for the variable/unit table, full conditional induction proof and directed oracle. H is downstream enforcement versus issuer retirement. T is the finite private-process fixture. D includes exact coverage, process/database/wire reconstruction, positive behaviors and candidate limits, plus all12 controls. C includes extra coordination and premature-new refusal; U includes authentication, concurrent resources, external irreversible effects, epoch reuse, DB loss/rollback, power loss and natural failure distributions.

The read-only auditor imports no actor/runner/policy implementation. It reconstructs issuer grants, committed resource state, local transaction journal and IPC chain from retained bytes and a separately authored directed outcome table. This same-author separate implementation/process is not independent human review. The finite directed matrix is not a population reliability estimate.

## Execution and implementation

Provided Linux x86_64 container; CPython3.13.5, SQLite3.46.1, standard library, private line-delimited stdio between persistent subprocesses. DELETE journal, synchronous FULL, busy_timeout0, explicit BEGIN IMMEDIATE/COMMIT, one writer per DB. Resource check, private effect INSERT and journal entry share one transaction; replies are emitted only after successful COMMIT. Resource never reads issuer DB or scoring records.

78 scientific actor processes:72 natural exit0 and6 planned abrupt exit23. Each RESOURCE_RESTART has a fresh process reopening the same DB. Six batch children and six outer supervisors exit0. All6 batches completed without timeout. Eight excluded actor-unit methods passed before freeze; their unit receipt is retained, but temporary per-unit actor files were removed by unittest cleanup and are not claimed retained. No full-matrix construction run preceded the formal allocation.

No GUI, keyboard/mouse/XTEST, model/provider, actual task action, user-data mutation, external experiment network or package installation. All effects are private diagnostic integer database entries. authority_granted=false and task_success=null; these fields do not mean the DB is physically unchanged. Process exit23 is not SIGKILL or power loss. CPU frequency is unpinned, no timing endpoint; no Docker/OrbStack image attestation. IPC timeouts are engineering limits, not latency results.

## Source-first chronology and preservation

Intake main b669264a65d1474481e511676eacfc06bf82d775. Source commit b82dc564bcafb15b9938064b0c305db3921eea88 contains all9 source/gate files. All9 exact Git blob IDs matched local bytes before Issue authorization comment5826661831 and formal case0. FREEZE SHA25677a0dcc760e6f5ec520504cc1ca3e33b8ec370c82634421553446c18c198ddcc. First-outcome comment5826700328 records the result before packaging.

Original RECORDS.json SHA256 e88b1f045a4a5831bcb0465fd74de0ac379b429c7f84513031876f37c97eac87. This file contains retained observations, not a regenerated simulation. Complete case/batch JSON, initial/final/restart SQLite bytes, original DB files, SQL traces, boots, exact request/reply strings, actual process waits and original audit/control receipts are retained. Corruption inputs are exactly reproducible from original records plus the frozen deterministic mutations and saved changed-byte hashes; temporary full mutated-record files were not retained. Read-only reconstruction re-creates only those data copies, never the scientific actors.

## Integration decision

For #24/#2789 recovery, treat issuer retirement, explicit resource installation and effect commit as separate milestones. A greatest-seen policy only promises exclusion after newer accepted work has reached that resource. Stronger installation-based exclusion needs an additional recipient operation and acknowledgment, retained across restart. Arbitrary GUI operations that cannot participate in the same check/effect transaction do not inherit this guarantee. No automatic runtime/default promotion or global ROADMAP closure follows.
