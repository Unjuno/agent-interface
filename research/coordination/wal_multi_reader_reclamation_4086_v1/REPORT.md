# Concurrent WAL reader reclamation boundary (#4116)

Decision: **PASS_MULTI_READER_RECLAMATION_BOUNDARY_SCOPED**.

## H
With multiple coherent WAL read snapshots, releasing only the reader associated with the current request is insufficient evidence that WAL storage is reclaimable. Reclamation depends on every active read transaction; checkpoint progress and full truncation are distinct.

## T
Provided Linux x86_64 execution container, CPython 3.13.5, SQLite 3.46.1; standard library only. Exact #531 model Git blob `24329aaedf166b98a5babf5cfb9c61af7c6f40f0`. WAL/FULL, page size4096, wal_autocheckpoint1, journal_size_limit16384. Six schedules x two fresh repetitions =12 cases, 64 writer transitions each =768. Separate writer and reader subprocesses; 12 writers and16 readers. Two immutable six-case formal batches; no rerun/replacement/exclusion/post-freeze source change.

## D / first outcome
- Audit: 780 checks, errors=[], 10/10 copied-evidence corruptions rejected.
- CURRENT_REQUEST_ONLY false-reclaimable classifications: **4** (both repetitions of RELEASE_YOUNG_KEEP_OLD and RELEASE_OLD_KEEP_YOUNG).
- ACTIVE_READER_REGISTRY false FULLY_RECLAIMED classifications: **0**.
- RELEASE_OLD_KEEP_YOUNG: TRUNCATE at write32 returned `[1,64,32]` in 2/2 cases: 32 frames checkpointed, but B remained active and WAL stayed 263,712 bytes. This is partial progress, not full reclamation.
- RELEASE_YOUNG_KEEP_OLD: releasing B while A remained produced `[1,64,0]`, WAL 263,712 bytes in 2/2.
- OLD_ONLY reached 527,392-byte WAL at write64; YOUNG_ONLY 395,552 bytes; both remained unreclaimed while their reader was active.
- NO_READERS and RELEASE_ALL reached WAL=0 with successful registered TRUNCATE in 2/2 each.
- After all owned readers were closed, cleanup TRUNCATE yielded WAL=0 in all12 cases.
- Every writer transition was APPLIED and every final logical history retained exactly two rows.
- Held reader snapshots retained their historical values; no historical snapshot is called current or action-authoritative.

## Construction history
construction-00 completed all six fixture cases but the pre-freeze auditor incorrectly required a reader released at write32 to keep returning its old database snapshot later. That audit assumption was retained as a construction HOLD. Only the audit interpretation changed before freeze: the copied retained view must remain exact, while only still-held readers must continue sampling the pinned snapshot. construction-01 then passed 6/6. Scientific schedule and gates did not change.

## C
This is a known SQLite WAL/checkpoint mechanism exercised through a new cooperative application resource-lifetime fixture, not a SQLite defect. One writer, at most two readers and a finite64-write horizon are assumptions. `CURRENT_REQUEST_ONLY` is an explicit negative comparator, not alleged production behavior.

## U
No power-loss durability, leaked foreign readers, many-reader scaling, concurrent writers, arbitrary schema, model/GUI/task utility, latency/token benefit, cross-platform transfer or production promotion. WAL sizes are apparent file extents, not physical disk use or write amplification. Same-author separate audit process is not independent human review.

## Integration handoff
Resource state should distinguish `REQUEST_RELEASED`, `PENDING_READERS`, checkpoint progress and `FULLY_RECLAIMED`. Copying historical evidence before releasing its DB transaction can preserve that historical evidence, but later consequential work still requires a fresh state/admission boundary.
