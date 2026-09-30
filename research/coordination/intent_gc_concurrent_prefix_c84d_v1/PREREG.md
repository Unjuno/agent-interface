# #4037: concurrent intent admission versus captured compaction prefix

Allocation `intent-gc-concurrent-prefix-c84d-20260922-01`.
Intake main e4c2e58122aa138e421048d8e86ec18259143b9e.
Only research/coordination/intent_gc_concurrent_prefix_c84d_v1/ is owned.

## H / T / D / C / U

H: an atomic compaction commit using a previously captured frontier can delete newer accepted history. Prefix-limited deletion preserves it; transaction-local frontier revalidation instead defers changed-state compaction.

T: exact unchanged #531 source, blob24329aaedf166b98a5babf5cfb9c61af7c6f40f0; provided Linux x86_64 container, CPython3.13.5/SQLite3.46.1, standard library. Private DELETE/FULL databases, read_uncommitted off, separate actor and persistent compactor processes. Only SQLite fixture transitions, no GUI/model/network/credentials. No Docker/OrbStack attestation. Three policies x three barrier-ordered schedules x two repetitions =18 cases/54 independent-copy probes. Each case has two original processes and three probe processes,90 formal workers total. Two fixed9-case batches. RPC and child-wait bounds3s; a persistent process spans the finite case, so3s is NOT a total process-lifetime claim. Batch supervisor25s, teardown allowance2s+2s; outer tool30s. Commands use the actual resolved interpreter with -S -B. Imports are stdlib; disabling site does not change the scientific model.

D: complete cases/sources/actual zero exits/DB bytes/SQL/process order must reconcile. The STALE_DELETE_ALL between cases must yield missing D4, REBOUND_D4 applied, GENUINE_E5 gap. Both candidates must refuse rebound D4 and admit E5 across all6 cases. REVALIDATE_FRONTIER must defer exactly2 between cases without mutation. All exact D4 requests avoid second effects. Complete controls pass; >=8 raw corruptions rejected. PASS_CONCURRENT_COMPACTION_PREFIX_SCOPED is a boundary finding, not acceptance of the negative comparator. Incomplete/source/exit evidence STOP/HOLD; complete gate contradiction FAIL. No formal retries, replacements, exclusions or threshold tuning. Stop whole allocation after first failed batch.

C: cooperative monotonic issuer, one current epoch, one compactor per case, stable current metadata. All three methods write marker+deletion in one transaction; this isolates stale deletion scope, not transaction atomicity. The compactor's capture transaction ends before the actor's next commit. SQLite correctly serializes individual transactions but does not automatically bind the later deletion to the earlier read. Declared directed interleavings are not natural race frequency.

U: no multi-compactor, issuer restart/ABA, power loss, arbitrary corruption, authenticated provenance, live application effects, model choices, performance or production generality. Exact ordinal/state comparisons; timestamps diagnostic. Calibrated combined uncertainty and coverage factor unavailable; no numerical reliability estimate from2 repeats. Independent auditor means separate implementation/process by the same author.

## Fixed schedule

Batch0 repetition0, batch1 repetition1. In each batch: ADMIT_BEFORE_CAPTURE, ADMIT_BETWEEN_CAPTURE_AND_COMPACT, ADMIT_AFTER_COMPACT; within each schedule: STALE_DELETE_ALL, BOUNDED_PREFIX, REVALIDATE_FRONTIER. Initial A1/B2/C3 under capacity2 leaves generation4/historyB2,C3/watermark1. D4 is applied in the named interval. Compactor captures4 in BEFORE and3 otherwise. All final states have one existing D4 effect. Independent copies probe exact D4(g4->g5), rebound D4(g5->g6), new E5(g5->g6); no production replay is authorized.

## Field/variable table

| Field | Meaning | SI unit | Definition | Domain / premise | Type |
|---|---|---|---|---|---|
| intent_seq | Issuer's operation ordinal | 1 (dimensionless) | A1 through E5 | positive integers, no reuse/new epoch in this study | scalar integer |
| generation | Current application generation | 1 | Initial1, increments on each admitted effect | positive integers; not a time | scalar integer |
| watermark | Retired ordinal upper bound | 1 | Independently retained state | nonnegative, monotonically MAX-updated | scalar integer |
| captured | Compactor's prepared accepted frontier | 1 | maximum of watermark and retained receipt ordinals |3 or4 in formal cases | scalar integer |
| receipts | Retained content-bound history | not applicable | complete six-field Receipt objects | at most2, ordered by intent_seq | list of records |
| effects | Independent fixture scoring log | not applicable | sequence/label/generation transitions | never read by candidate admission | list of records |
| started_ns / ended_ns | Monotonic observation brackets | s, stored10^-9 s | monotonic_ns in one container | nonnegative integers, comparable same domain | scalar integer |
| rep / index | Coverage labels |1 | fixed schedule above | rep0,1; index0..8 | scalar integer |

Unit check: only dimensionless ordinal values are compared with ordinal values; generation is compared with generation. No timestamp creates a frontier or grants authority. For example frontier3 cannot justify deleting D4 unless later validation explicitly covers4.

## Roadmap / publication

Retained predecessor read-only re-audit -> excluded construction -> public hash/source commitment -> two first-outcome batches -> independent raw/database audit and corruptions -> full NEW source/evidence PR -> exact-head checks/main readback. Prior a61e archive remains separate; no old row is pooled. Parents/global roadmap are not completed here. Engineering incidents stay under #4037.

SQLite primary references: https://www.sqlite.org/isolation.html and https://www.sqlite.org/lang_transaction.html . Known application-design principle, no vulnerability or novelty allegation.
