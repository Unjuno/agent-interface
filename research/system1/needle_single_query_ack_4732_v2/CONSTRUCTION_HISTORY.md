# Construction history — successor Issue #4813

Allocation `needle-single-query-ack-6911201-6911301-6911401-v2`; formal seeds have not run. Both construction runs use seed `6911101`, separate output/volume directories, and are excluded from formal inference.

## Environment

- Docker Desktop client/server 29.8.0; cached `needle-pilot05:local`, Linux/amd64, image ID `sha256:6ab7a93188dd60d3832a0be8b5266418e0de1253159c5c66e64562a85fd4a10e`.
- CPU only; no network/pull, read-only root/source, 1 CPU, 2 GiB, 64 PIDs, no-new-privileges, bounded tmpfs.
- Frozen #4714 source mounted read-only. Its Git blob is `b055bd949a4489fc25e10b40ff7e6a44e233fb86`; SHA-256 is `14d403f5f394fc4ac228609c5c137f09c153b777a45cedfe4abd895ff72ebf74`.

## Construction A — before receipt handshake

Docker contract tests passed 6/6. Separate auditor returned `CONSTRUCTION_AUDIT_PASS`: 24/24 arm-arrivals exact, errors 0, 5/5 corruption controls rejected. Ack p95: INLINE_512 34.474455 ms, ONLINE_QUERY_ONLY 41.363101 ms, ratio 1.199819. Stage p95 (inline/query-only): update 6.861494/3.252720 ms, commit 21.345373/31.483664 ms, full batch 1.937768/0.935240 ms, single query 0.113234 ms. Total arm elapsed 583.445197/583.808479 ms.

## Measurement-boundary correction and Construction B

Predecessor PR #4740 review identified that the worker began post-ack full-batch inference immediately after flushing ACK; on a shared one-CPU quota that could compete with supervisor ACK receipt/parsing included in request→ack timing. Before formal freeze, runner was amended: supervisor sends `ACK_RECEIVED` only after ACK has been read and parsed; worker waits for that message before starting the post-ack audit. This fixes the identified scheduling overlap while preserving response content and matched model state. It is recorded as a pre-freeze protocol amendment.

The same six Docker contract tests passed after amendment. Fresh-output Construction B separate auditor returned `CONSTRUCTION_AUDIT_PASS`: 24/24 arrivals, errors 0, 5/5 controls rejected. Ack p95: INLINE_512 27.485479 ms, ONLINE_QUERY_ONLY 25.529501 ms, ratio 0.928836. Stage p95: update 7.546580/3.074066 ms, commit 17.029206/19.247308 ms, full batch 1.049625/0.735349 ms, one query 0.099851 ms. Total arm elapsed 523.451725/563.029430 ms. This is still one construction seed, not evidence of a formal effect.

Both unmodified raw reports, exact worker inputs, independent audits and actual final-volume snapshots are retained in `construction/`; raw reports use ordered 10,000-character text chunks because the GitHub MCP content reader truncates large files at 200,103 characters. Each chunk's Git blob was checked against the corresponding local bytes; manifest binds reconstructed size and SHA-256. An earlier incomplete `run.json` upload is replaced by an explicit non-evidence pointer.

## Freeze boundary

Formal allocation remains unused. Formal work requires final source and preregistration hashes, GitHub readback verification, issue-body identity, collision checks, and fresh empty paths/volume. No formal trainer or auditor command has been invoked.
