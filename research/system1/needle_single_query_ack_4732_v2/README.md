# Needle single-query acknowledgement — successor #4813

This fresh allocation follows #4732, whose frozen audit stopped on a schema error and whose separate post-hoc replay missed the latency-ratio gate on all three seeds. It keeps that history unchanged.

## Current disposition

Construction seed `6911101` only: Docker unit tests passed 6/6; independent construction audit passed 24/24 arm-arrivals, zero integrity errors, and 5/5 corruption controls rejected. Construction ack p95 was 34.474455 ms INLINE_512 vs 41.363101 ms ONLINE_QUERY_ONLY (ratio 1.199819). This single construction seed does not support the latency-improvement hypothesis and is not formal evidence. Formal seeds `6911201`, `6911301`, `6911401` remain unused.

## Scope and known measurement limitation

This is a synthetic local CPU adapter and local durable snapshot timing study, not Cactus Needle 3 adaptation quality or task/action readiness. In predecessor PR #4740, code review noted that the worker started the post-ack full-batch audit immediately after flushing ACK, which could overlap timed supervisor receipt/parsing on one CPU. Before formal freeze, v2 added an explicit `ACK_RECEIVED` handshake and reran construction B; preregistration and construction history record the amendment and result. No formal run has begun.

## Reproducibility

- `runner.py`, `audit.py`, and `test_study.py` are the new v2 source.
- `baseline/study.py` is byte-identical to #4714's immutable source: Git blob `b055bd949a4489fc25e10b40ff7e6a44e233fb86`, SHA-256 `14d403f5f394fc4ac228609c5c137f09c153b777a45cedfe4abd895ff72ebf74`.
- `CONSTRUCTION_MANIFEST.json` binds all construction raw/audit/volume snapshots.
- `FREEZE.json` and `PREREGISTRATION.md` govern any later formal run. Formal is not authorized until handshake/design, GitHub exact readback, collision, source hash, image digest, and empty output/volume checks all pass.

All predecessor outcomes and source files remain unchanged.
