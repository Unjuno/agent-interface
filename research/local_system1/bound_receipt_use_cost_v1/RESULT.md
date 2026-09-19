# Bound typed receipt use-cost formal result

Decision: **PASS_BOUND_TYPED_RECEIPT_USE_SCOPED**.

Frozen task `LOCAL-SYSTEM1-BOUND-RECEIPT-USE-COST-20260917-001` ran exactly one formal invocation with reruns0. The corpus contained 2,048 static receipts ×4 current variants =8,192 correctness queries, then 65,536 measured calls per arm after warmup, with single-CPU affinity and GC disabled equally only during measured loops.

- `JSON_STATIC_EACH_CALL` p95: **7.060 µs**.
- `BOUND_TYPED_STATIC` p95: **0.390 µs**.
- p95 ratio: **0.055241** (~18.1× lower p95 use latency).
- compile p95: **10.2615 µs**.
- p95 break-even reuse: **1.538 uses**.
- correctness: JSON errors0, bound errors0, exact truth/output hashes equal.
- static malformed controls rejected5/5; dynamic stale/currentness controls rejected8/8.
- network calls0, gradient updates0, task-input calls0, authority grants0.
- independent read-only audit: PASS; gate errors `[]`.

Result SHA-256: `9f579bfd16446b6322128ac42f6c046e3383a5b09ceea1f788cefae09ac6368c`.
Raw compressed latency SHA-256: `0446a2d63b561f8e0db7c46e5c8009df6b68c8483dbe5379f7ac011374f0da99`.

Scope: CPython 3.13.5 on one container host, trusted-local immutable typed object representation. This does not authenticate hostile memory, include screenshot/perception parsing, IPC, model reasoning, production ABI cost, or justify caching dynamic currentness.
