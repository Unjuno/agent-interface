# Passive-reader pagination cost — Issue 3985

## Result and delivery boundary

One source-frozen, four-batch allocation completed all 36 measurement cases and 9 capacity controls. All four batch supervisors and all 37 workers have actual exit 0; no retry, replacement or source tuning occurred. A separate raw-only auditor returned exit 0 with zero errors and rejected 10/10 corruption controls.

**Scientific decisions:** PASS_PAGINATION_WORK_LAW_SCOPED; PASS_LOCAL_BATCHING_TIME_SCOPED.

**GitHub delivery status: HOLD_FULL_RAW_PUBLICATION.** This staged PR publishes the frozen source/plan, environment, summary, audit output and integrity manifest. The complete original per-call responses, streams and timing/counter journals are retained in a checksummed conversation attachment, not yet committed here. Therefore this PR is Draft, is NOT independently re-auditable from GitHub alone, must NOT merge or close the Issue until the exact raw bundle is attached through a durable repository-accessible path, and establishes no production promotion. A hash or summary alone is not a downloadable raw-evidence claim.

## Measurements

Environment: supplied Linux 6.18.44 x86_64 execution container; CPython 3.13.5; AMD EPYC 9V74 virtual CPU description; five allowed CPUs (0–4), no physical isolation/frequency pinning; warm local regular files; 256 bytes/line. Three separate processes per size/page, Latin rotation. One uninstrumented drain plus explicit empty check is timed; a second declared instrumented pass separately counts logical reads/hash arguments. No Docker CLI/image identity; no Docker/OrbStack replication, network-none isolation, disk-throughput, model/GUI or user-visible latency claim.

| Records | Page | Wall median (ms) | Wall range (ms), 3 repetitions | Logical read bytes | SHA256 argument bytes |
|---:|---:|---:|---:|---:|---:|
| 128 | 1 | 6.858339 | 6.810037–7.028770 | 4227072 | 4259840 |
| 128 | 8 | 1.483135 | 1.444689–1.550645 | 557056 | 589824 |
| 128 | 32 | 0.873137 | 0.857894–0.984060 | 163840 | 196608 |
| 256 | 1 | 21.307702 | 21.258509–22.458307 | 16842752 | 16908288 |
| 256 | 8 | 4.176485 | 3.785910–4.621520 | 2162688 | 2228224 |
| 256 | 32 | 1.896876 | 1.857668–2.021640 | 589824 | 655360 |
| 512 | 1 | 77.198491 | 74.576441–80.332967 | 67239936 | 67371008 |
| 512 | 8 | 12.225327 | 12.206089–12.436257 | 8519680 | 8650752 |
| 512 | 32 | 5.421710 | 4.572499–5.540504 | 2228224 | 2359296 |
| 1024 | 1 | 288.974370 | 282.115152–294.989141 | 268697600 | 268959744 |
| 1024 | 8 | 41.679734 | 40.863076–47.094366 | 33816576 | 34078720 |
| 1024 | 32 | 12.758843 | 12.595653–13.215967 | 8650752 | 8912896 |

At 1,024 records, the median page1/page32 ratio is 22.648947870900205 (frozen threshold: 2). Both pages return the exact same ordered payloads with no authority, ACK or input. This does not establish a latency benefit for a live producer or the model: all source records already exist, no wait-for-batch cost is measured, and model/presentation/IPC/startup are outside the timed endpoint.

Capacity controls: three exact-1,024-byte cases succeed. All six 1,025-byte cases refuse STREAM_READ_BOUND_EXCEEDED, including the three with a previously obtained 512-byte consumed-prefix cursor. Appending one byte beyond the whole-log cap blocks the read even with a small unread suffix; no source truncation, cursor reset or automatic backpressure is added.

## H/T/D/C/U and complete analytical proof

See frozen PLAN.md, which contains the complete variable table, finite read/hash derivation, dimension checks, allocation and stop rules. Logical read bytes and SHA256 argument bytes are not physical disk reads or model tokens. Timing uncertainty is descriptive min/median/max over three repetitions; calibrated combined uncertainty and coverage factor are unavailable. No percentile/population generalization is made.

## Provenance and safe re-audit

Base main: b2457b746a6df06f6536585dfe2ab937aff639f4. Reader Git blob: ea72c166c2cea511ea91031dfbb14563fe4e3245; ledger: fb50be9d4d821a7836e6a0158c53a983f0f91df5. Exact frozen source is unchanged. Freeze SHA256: 372aad2e63df7343f650cbcf6b4a6d67e405b702e51b122e8314c42c3d6cffcb. Audit stdout SHA256: 7d0449f80214110965c03c594569fba9f08c5cada32d211da5381c378d93aff5.

The freeze was posted before any formal call in Issue #3985 comment 5766570106. First outcome was posted in comment 5766607302. Initial create_issue failed by disconnected response; two exact-title searches returned no match, and the confirmed next call created #3985. This is a publication incident, not a study rerun.

After restoring the ORIGINAL raw bundle beside these frozen files, audit only:
```sh
python -B audit.py formal-01 --controls
```
Do not invoke study.py/batch.py/supervise.py with consumed formal identities. Files under construction-01 are the separately excluded 64-record/page4 construction; no earlier crash-study rows are pooled. The upstream files were carried from the earlier attached bundle but their Git object IDs independently match the current pinned main.

## Integration handoff

For #3876, size the entire retained session rather than only the unread page, and account for repeated prefix reads/hashes when choosing already-available notification page sizes. Larger pages do not solve whole-log capacity, producer backpressure, ACK, host retention or epoch identity. Do not create another queue or change the existing default of 32 from this study. Any sealed-segment/checkpoint proposal needs a separate source/mutation/epoch contract and held-out live host validation.

Related disciplines: algorithm analysis (exact cumulative work), operating systems (page-cache versus storage traffic), and experimental design (paired conditions, measurement endpoints and scoped uncertainty). These are interpretation links, not extra verified application claims.

## Roadmap and preservation

Source reconstruction, analytic derivation, construction, preregistration, four formal batches and local raw audit: complete. Full GitHub raw publication, independent repository-only re-audit, PR review/checks and main integration: incomplete. Keep this branch because the Draft PR depends on it. Other branches and shared runtime/root files remain untouched. Closed #717, #3931/#3955/#3968 and all other parallel studies remain unchanged. #3876/#57 and the broad ROADMAP remain open.
