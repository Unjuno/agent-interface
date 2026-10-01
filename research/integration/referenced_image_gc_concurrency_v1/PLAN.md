# Issue #4144 — referenced-image GC concurrency v1

## H
A GC policy that scans reclaim candidates before its deletion transaction can delete a stale candidate after a new unacknowledged page begins referencing the blob. Re-evaluating zero-live-reference inside the same BEGIN IMMEDIATE transaction that deletes the blob should preserve the new page while collecting true orphans.

## T
Two policies: STALE_SCAN_DELETE and TXN_REVALIDATE_DELETE. Four barrier-directed schedules: PRODUCER_BEFORE_SCAN, PRODUCER_BETWEEN_SCAN_DELETE, PRODUCER_AFTER_DELETE, NO_NEW_REFERENCE. Three formal repetitions, separated into three immutable 8-case batches. Producer, GC scan and GC deletion are separate subprocess operations; explicit parent ordering supplies the barrier, never sleeps/random timing. Actor operation timeout 3 s; whole case worker timeout 12 s. Private SQLite only. Construction is excluded.

## D
PASS_REFERENCED_IMAGE_GC_CONCURRENCY_SCOPED iff all 24 formal first outcomes reconcile; the stale policy breaks page2 resolution in all three BETWEEN cases; the candidate has zero unresolved unACK references; both keep live A when producer is before scan; both collect A with no new reference; producer-after-delete restores verified A and page2 resolves; actor/process identities and neutral authority reconcile; independent raw-only audit has zero errors and >=8 corruption controls reject. Complete contradiction is FAIL. Missing source/process/denominator/audit evidence is STOP/HOLD.

## C
Trusted one epoch, exact content-addressed blob identity, serialized SQLite writers, correct producer bytes and one local database are assumptions. Transactional revalidation is the changed factor, not SQLite atomicity itself.

## U
No crash/power-loss, distributed/multi-database GC, hostile producer/ACK authentication, TTL policy, model viewing, exactly-once delivery, performance/token/task benefit or production promotion. Directed schedules are finite coverage, not race-frequency estimates.
