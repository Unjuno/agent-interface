# Resource-installed epoch fence vs greatest-seen tokens — #4349

Allocation `resource-fence-f13-20260925-01`. Base `b669264a65d1474481e511676eacfc06bf82d775`.
Own branch `research/resource-fence-20260925-f13`; path `research/coordination/resource_fence_f13_v1/`.
This new first-outcome experiment changes #4344's no-outstanding-grants assumption. Closed #544/#24/#628 and active #4037/#4299/#4332/#4335 are preserved. No blocked publication source is copied. Intake checked main, README, active CURRENT_GOAL, ROADMAP, recent open Issues/PRs, first100 branches, closed resource-fencing lineage and targeted searches. Coverage is bounded/non-atomic, not a global ownership oracle.

## H / T / D / C / U

H: issuer retirement is not downstream revocation. A maximum of previously accepted tokens can reject older work only after the resource has seen higher work. Installing a resource epoch before acknowledging that installation can reject old outstanding requests even without new work, including after resource restart. It cannot retroactively cancel earlier effects.

T: 36 private cases = six scenarios x three modes x two repetitions. Every case uses separate issuer and resource processes/databases; resource never reads issuer storage. STABLE, IDLE_RETIRE, NEW_FIRST, DELAYED_FENCE, PREINSTALL_NEW, RESOURCE_RESTART. Modes ISSUER_ONLY, MAX_SEEN, INSTALLED_EPOCH. Epochs7 and8 are authored integers, not clocks. Two old grants are issued at7; the issuer may retire to8. Only INSTALLED_EPOCH has the additional install request/response. All modes share scope/type/ID checks and resource-local atomic check/effect/journal transactions. Effects are private integer database entries, not GUI or input authority. Six immutable six-case batches, each invoked once. Retain source hashes, IPC bytes and monotonic brackets, SQL, initial/final/restart DB bytes, boots/PIDs/real exits, all first outputs. No retries/replacements/exclusions/postfreeze tuning. Separate short actor unit construction precedes public freeze; there is no full-matrix construction replay. Stop on an incomplete batch. These are technical directed repetitions, not statistical samples of natural failure incidence.

D: PASS_RESOURCE_FENCE_BOUNDARY_SCOPED requires36 cases/72 effect requests, actual process/batch receipts, source and DB/IPC agreement and the exact table below. Candidate post-resource-install old effects=0; candidate pre-fence old effects=2 are REQUIRED limitations, not hidden. Candidate premature-new refusals=2. All stable and distinct fresh post-installation requests apply. Independent raw-only audit errors=[] and12/12 effective well-formed evidence mutations reject normally. A complete contradiction is FAIL; missing source/coverage/process/evidence/control integrity is HOLD/STOP. No promotion from counts alone.

C: maximum-seen fencing provides ordering after a higher observed token, not immediate issuer revocation. It is a valid weaker contract, not a production defect. Installation adds protocol messages and may refuse early new work; no performance advantage is claimed. Cooperative single effect owner, trusted monotonically advancing issuer, immutable scope/ID/contents, no DB rollback/loss, and all effects passing the resource's transaction are essential. Separate databases are not a distributed atomic transaction. The deliberately staged interleavings are not adversarial traffic.

U: no authentication, arbitrary GUI fencing, in-flight external irreversible effects, split brain, multiple resources/owners, failover election, power-loss, epoch reuse/rollback, natural distributions, model/task/token/latency/energy benefit. Same-author separate implementation/process audit is not external human review. No calibrated combined uncertainty u_c or coverage factor k is available; do not invent either. Runtime and global ROADMAP remain open.

## Frozen directed oracle

A = APPLIED; O = OLD_TOKEN; W = WRONG_EPOCH. Entries are in exact per-case request order.

| Scenario | Request IDs | ISSUER_ONLY | MAX_SEEN | INSTALLED_EPOCH |
|---|---|---|---|---|
| STABLE | old-A | A | A | A |
| IDLE_RETIRE | old-A | A | A | W |
| NEW_FIRST | new-A,old-A | A,A | A,O | A,W |
| DELAYED_FENCE | old-A,old-B,new-A | A,A,A | A,A,A | A,W,A |
| PREINSTALL_NEW | new-A,new-B,old-A | A,A,A | A,A,O | W,A,W |
| RESOURCE_RESTART | old-A,new-A | A,A | A,A | W,A |

Issuer retires before the first resource APPLY except STABLE. Candidate INSTALL is before all resource APPLYs in IDLE_RETIRE/NEW_FIRST/RESOURCE_RESTART, after first APPLY in DELAYED_FENCE/PREINSTALL_NEW, and absent in STABLE. Other modes do not receive INSTALL. Restart is a completed resource command followed by owned abrupt exit23; a fresh process opens the SAME database before further work. This is process-restart retention, NOT a power-loss experiment. Six abrupt exits23 and72 natural exits0 are expected from78 actor processes; six batch processes also need observed exit0. Requests old-A/old-B use values11/12; new-A/new-B use21. Values are diagnostic integers, not resource sizes.

## Environment and implementation

Provided Linux x86_64 container, CPython3.13.5, SQLite3.46.1, standard library, stdio line protocol. DELETE journal, synchronous FULL, busy_timeout0, explicit BEGIN IMMEDIATE/COMMIT, one writer per database. CPU affinity/frequency and tool availability are in ENVIRONMENT.json; no pinned clock or Docker/OrbStack attestation. No new GUI, model/provider, task input, package install, user data or experiment network. Child protocol wait3s, batch outer wait25s; limits are engineering safeguards, not measured performance. Actual queries may copy a database for inspection; original retained bytes are never modified by the auditor.

## Variables / units

All protocol state is exact integer/string data. SI unit1 means dimensionless.

| Symbol | Meaning (Japanese) | SI unit | Definition | Domain / assumptions | Type |
|---|---|---|---|---|---|
| s | 受付スコープ | 1 | Unique per-case scope string | Trusted, unchanged | string |
| i | 要求ID | 1 | ID within scope | Immutable content, no reuse | string |
| e | 要求の世代 | 1 | Epoch attached by issuer | Positive integer | scalar integer |
| c | 発行側の現在世代 | 1 | Issuer committed epoch | 7 then8 | scalar integer |
| r | 実行先の設定済み世代 | 1 | Resource committed epoch | Starts7; explicit install to8 | scalar integer |
| h | 実行先が受理済みの最大世代 | 1 | Maximum of initial7 and accepted token epochs | Monotone | scalar integer |
| v | 私有DBへ保存する値 | 1 | Request's fixed diagnostic value | 11,12,21 | scalar integer |
| E | 適用済み要求集合 | 1 | Resource entries keyed by i | Finite, content-bound | finite map |
| j | 実行先処理の順序番号 | 1 | Local transaction order | Nonnegative integer | scalar integer |
| t | IPCの単調時計値 | s | monotonic_ns divided by10^9 | Same host, diagnostic only | scalar real |

## Conditional proof

The common scope/type/duplicate checks run first. For fresh well-formed requests, ISSUER_ONLY accepts irrespective of e; MAX_SEEN accepts exactly when e>=h then updates h to max(h,e); INSTALLED_EPOCH accepts exactly when e=r. Successful installation changes r from7 to8 inside the same serialized transaction system used by application of a request. The explicit mode does not infer r from a request.

Let transaction j be the successful installation of8. Immediately after its COMMIT, r=8. For any later transaction, a refused request does not change r, an accepted request changes only E/h and not r, and a further installation may only increase r. By induction every later resource state has r>=8. An old request has e=7; hence e cannot equal r, so it cannot enter E. A restart reopens the same committed meta row, preserving this induction. This proves exclusion only AFTER resource installation, assuming all effects use this check and the same serialized durable state.

The issuer's c is not read by the resource, so changing c alone leaves r and h unchanged. In IDLE_RETIRE, c=8 while r=h=7. The old e=7 passes MAX_SEEN and ISSUER_ONLY; it fails the explicit mode only because that mode first commits r=8. This is an information/coordination distinction, not a missing cryptographic test.

In NEW_FIRST, the new e=8 request makes h=8 before old e=7 arrives. MAX_SEEN therefore rejects the later old request, proving the weaker positive ordering property. In DELAYED_FENCE, old e=7 arrives while r=7 and is allowed even by the candidate; a later fence cannot undo E. In PREINSTALL_NEW, e=8 arrives while r=7 and is refused by the candidate: this intentional availability cost is required by the equality contract. A distinct new request after installation is allowed.

Dimension check: all equality/order/max operations compare dimensionless integer epochs. No epoch is compared with a clock or a byte quantity. A count of effects is not elapsed time, bytes or task success. Example c=8,r=h=7,e=7 satisfies e>=h, but after r:=8 violates e=r.

## Roadmap and reproduction boundary

Construction -> publish exact source/gates and read back -> six first-outcome batches -> separate raw audit and12 controls -> complete evidence plus report -> exact remote readback/readonly restoration -> applicable CI/scoped review -> evidence-only main integration. Keep first results/failures intact. Cleanup only owned dependency-safe refs via supported operations. Concrete #24/#2789 decision: controller retirement, resource fence receipt and accepted effect are three different milestones. Do not reuse an issuer receipt as proof of downstream exclusion.

Primary background: Mike Burrows, The Chubby lock service for loosely-coupled distributed systems, OSDI2006 section2.4, https://static.usenix.org/events/osdi06/tech/full_papers/burrows/burrows_html/ . It describes recipient validation, including the weaker latest-observed sequencer alternative; it does not establish this implementation. SQLite isolation: https://www.sqlite.org/isolation.html . These are known mechanisms applied to a scoped interface boundary, not a claimed new distributed-lock algorithm.
