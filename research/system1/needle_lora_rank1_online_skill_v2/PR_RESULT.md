# Rank-1 online LoRA v2 formal result — Issue #4507

Disposition: **FAIL_RANK1_SKILL_CAPACITY**. The one-shot training and independent audit completed; the audit had zero integrity errors. This is the preregistered quality FAIL, not an execution STOP.

| Seed | Rank-1 held-out B accuracy | Rank-2 held-out B accuracy | Role-A accuracy |
|---:|---:|---:|---:|
| 74111 | 0.909180 | 0.909668 | 0.966797 |
| 74222 | 0.935791 | 0.936035 | 0.965332 |
| 74333 | 0.894287 | 0.896729 | 0.951416 |

Seed 74333 missed the preregistered rank-1 per-seed minimum of 0.90. Aggregate update-only p95 was 2.254438 ms for rank-1 versus 2.208662 ms for rank-2 over 48 measurements (ratio 1.020726), missing the preregistered <=0.80 speed-benefit ratio. No retry, seed substitution, or post-result tuning occurred.

Execution: one formal Docker orchestration with pinned image `sha256:6ab7a93188dd60d3832a0be8b5266418e0de1253159c5c66e64562a85fd4a10e`, linux/amd64 CPU-only, network disabled, read-only root/source, 1 CPU / 2 GiB / 64 pids. Training and audit exit codes were 0. PyTorch emitted a NumPy initialization warning because NumPy is absent; the independent audit passed with errors=[].

Full audit, invocation/host capture, logs, checksums, and raw per-seed JSON are retained in `formal/alloc-02/RAW_TRAINING.zip`, SHA-256 `7a739e80b282cbe8943f4b1897bbde0c7373d7a55cd1d4823e99abe9ca4a65e3`. Each uploaded evidence Git blob SHA was fetched back and matched.

Scope: synthetic bounded online-adaptation task only. This does not establish real pretrained Needle behavior, production real-time tuning, real retrieval needle-in-haystack accuracy, task-effect improvement, or role-network/skill integration. The consumed v1 STOP remains separate and unchanged.