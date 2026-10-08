# Referenced-image GC concurrency — Issue #4144

Disposition: **PASS_REFERENCED_IMAGE_GC_CONCURRENCY_SCOPED**.

Three prospectively frozen 8-case formal batches ran once each. All24 worker subprocesses and66 producer/GC actor operations exited0. Independent raw-only audit reconstructs24/24 with errors=[];10/10 corruption controls reject. Scientific source hashes remain identical to the public preformal freeze.

The unsafe STALE_SCAN_DELETE policy produced exactly one unresolved unacknowledged page2 reference in each of the three PRODUCER_BETWEEN_SCAN_DELETE repetitions (3/3). The candidate TXN_REVALIDATE_DELETE produced zero unresolved unacknowledged references across all12 candidate cases and all three between-scan interleavings.

Both policies kept a live blob when producer committed before scan, reclaimed it when no new reference existed, and allowed a producer after deletion to restore verified exact bytes so page2 resolved. Authority remained none and no task input was dispatched.

Construction remains excluded: v0 raw audit passed but first corruption suite rejected only8/9; v1 stopped at the inherited outer3s worker envelope after subprocess separation; v2 used actor<=3s / worker<=12s, completed8/8, audit PASS, controls10/10. Formal remained0 until the exact v2 source/FREEZE blobs were published to GitHub.

Scope: trusted single epoch, exact content-addressed blob identity, one local SQLite DB, serialized writers. No crash/power-loss, distributed/multi-database GC, hostile producer/ACK authentication, model viewing, exactly-once delivery, TTL sizing, performance/token/task benefit or production promotion.
