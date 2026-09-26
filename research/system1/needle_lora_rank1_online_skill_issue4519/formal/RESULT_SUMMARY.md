# Issue #4519 formal result

Allocation: needle-lora-rank1-online-skill-v2. One formal invocation, zero retries. Local CPU-only Docker image sha256:6ab7a93188dd60d3832a0be8b5266418e0de1253159c5c66e64562a85fd4a10e (linux/amd64), network none, read-only root/source, 1 CPU, 2 GiB, 64 PIDs.

Decision: FAIL_RANK1_SKILL_CAPACITY. Independent audit: PASS_AUDIT, zero audit errors. Three fresh seeds 75111, 75222, 75333 completed. Rank-1 update p95 3.771978 ms; rank-2 p95 2.718426 ms. This does not support rank-1 deployment; it failed the preregistered skill-capacity criterion.

Exact per-seed records are retained locally with hashes in OUTPUT_MANIFEST.json:
- seed-75111.json: 221956 bytes, d2b437c74f14748484d1258c5e773e28ff63934dc83935915050cf4a5c991960
- seed-75222.json: 221855 bytes, 1bd2136e40ef36f672bc1be64d5c15b7312620274fd86ab8281cd37547f87226
- seed-75333.json: 222102 bytes, b2209c9df6b3e3b6f264bac2d502c1f1611f860afbe0ec2e853a0cfcf62c30b1

Harness history: two entry checks stopped before the formal invocation marker and before any container started: first because the runner requires an empty output directory or its exact frozen invocation marker; second because the freeze sidecar format included an unsupported filename suffix. Both were corrected, construction tests passed 6/6 on host and Docker, and pinned source/image hashes were verified before the single formal run. No training/audit container ran during those preflight stops.