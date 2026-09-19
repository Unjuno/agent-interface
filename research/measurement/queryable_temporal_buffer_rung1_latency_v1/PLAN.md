# Queryable Temporal Buffer Rung 1 — Latency/Boundary

TASK: QUERYABLE-TEMPORAL-BUFFER-RUNG1-LATENCY-20260918-001
PARENT: #1028
BASE: e0f1f215890d8626ac012c5ee924075b4a2c2926

H: Continuous retention changes only temporal availability. With replay-capable source history, JIT and ring must return identical historical source IDs and both require zero acquisition boundary. With a live-only source, the ring can return already-past requested evidence immediately while JIT cannot reconstruct that past; a separately labelled future-equivalent JIT burst must wait one horizon and one acquisition boundary.

T: Python stdlib, fixed 5 ms cadence, 50 ms horizon, max 6 frames, 4096-byte synthetic payload, >=100 ms warmup, 64 REPLAY_CAPABLE pairs + 64 LIVE_ONLY pairs, seed 103820260918001. Parent Rung0 source pinned. One formal invocation after source-first publication and ownership reread.

D: exact replay frame/payload identity64/64; live ring past available64/64; live JIT exact past available0/64; future-equivalent JIT boundary64/64; ring p95<=10 ms; future JIT p50>=45 ms; paired median future-JIT minus ring>=35 ms; no current-role/authority escape; source/audit integrity; reruns0.

C: live-only advantage is availability, not necessarily indexing speed. Replay-capable sources can erase acquisition advantage. Synthetic payloads understate real capture/encoding/privacy costs.

U: same-host synthetic source only; no model/task/token/frontier-boundary or production claim.
