# Issue #4714 construction and preflight history

Allocation `needle-native-volume-checkpoint-6842731-6842733-6842737-v1`. Formal seeds remain unused. All named volumes below are separate local Docker volumes labeled `codex.issue=4714`; none is the future formal volume. Failed outputs and volumes are retained, not overwritten or removed.

## Shared environment

- Docker 29.8.0 client/server, cached `needle-pilot05:local`, image `sha256:6ab7a93188dd60d3832a0be8b5266418e0de1253159c5c66e64562a85fd4a10e`, Linux/amd64, Python 3.12.14, PyTorch 2.5.1+cpu on WSL2.
- No image pull/install; containers use network none, read-only root and source, one CPU, 2 GiB, 64 PIDs, no-new-privileges, 128 MiB `/tmp`.
- All construction executions use the separate construction seed 6842703; no 6842731/33/37 formal seed has run.

## Runner bring-up failures

- First native-volume construction attempt on seed 6842701 exited 1 while reading resident READY; stderr was discarded by the prototype. Its bind output/volume are retained as `construction`.
- Second attempt captured the cause: child resident process inherited argparse's required `--volume-root` option and exited before READY. The runner parser was changed to require the path only for top-level orchestration. Seed 6842701 partial output and v2 volume remain retained.
- First attempt on seed 6842703 failed before running with `IndentationError` introduced by the prediction-timing instrumentation patch. No training or arrival occurred.
- After correction, final-source Docker tests passed 5/5 and AST parsing passed. `construction-v5` completed seed 6842703 across both resident arms ×12 arrivals; request, snapshot, prediction and actual final volume bytes independently audited with 24/24 checks, 0 errors, 5/5 corruption controls rejected. Disposition: `CONSTRUCTION_ONLY_AUDIT_PASS`.

## Full-path construction result (not formal)

Arm order was volume then bind. Resident p95 request→ack: volume 181.310 ms, bind 148.593 ms. Durable-commit p50/p95: volume 15.578/18.788 ms, bind 33.602/105.506 ms. Adapter-update p50: volume 2.939 ms, bind 2.107 ms. Held-out prediction p50/p95: volume 1.517/79.188 ms, bind 0.626/44.213 ms. Worker startup: volume 1,534.5 ms, bind 1,466.2 ms. The native volume greatly reduced commit latency in this construction seed but did not reduce total request→ack; it was slower and both arms exceeded 60 ms. This is one unallocated construction seed and does not establish the direction or gate outcome for the three formal seeds.

Earlier seed 6842701 construction before prediction timing showed volume/bind request→ack p95 179.795/183.446 ms, commit p50 11.872/96.007 ms, and 24/24 independent audit checks. That earlier run is retained only as bring-up evidence and is not used for a matched-seed claim.

## Freeze boundary

At this history's initial publication, formal source is not frozen and no formal container has been started. A construction full-path run is explicitly excluded from formal evidence. Formal work may proceed once source hashes, image ID, branch/path, command and current-main collision checks are published/read back exactly; then it is one orchestration with no retry or seed replacement.
