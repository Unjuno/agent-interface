# Issue #4884 — three-seed role-C support-count replication

## Disposition

`PASS_REPLICATION_SIGNAL_WITHIN_FROZEN_DESCRIPTIVE_GATE`: the independent audit passed all 18 role cells; support prefixes were exact in all seeds; A/B states and outputs were exactly unchanged in all paired arms; role-C support64 improved held-out accuracy in 2/3 seeds, meeting the preregistered directional gate. The third seed regressed. This is descriptive evidence for one synthetic family at n=3, not a significance or population estimate.

## Formal outcomes

| Seed | C support16 | C support64 | Paired delta | A/B exact |
|---:|---:|---:|---:|:---:|
| 7867401 | 0.936767578125 | 0.963134765625 | +0.0263671875 | yes |
| 7867601 | 0.91943359375 | 0.962646484375 | +0.043212890625 | yes |
| 7867801 | 0.9599609375 | 0.93994140625 | −0.02001953125 | yes |

Positive seeds: 2/3. Median paired delta: +0.0263671875. Role A accuracy was 0.969482421875, 0.968017578125, 0.966796875 respectively and identical between paired arms; role B accuracy was 0.939208984375, 0.947265625, 0.948486328125 and identical between paired arms. Base weights remained immutable in all six arms.

Every seed used 400 base updates, 120 role-B updates and 120 role-C updates in each arm. Held-out N=4096 per role/seed. PyTorch 2.5.1+cpu, deterministic algorithms, one thread, CPU. Image and source identities are in `FREEZE.json`; exact commands and the pre-training wrapper smoke are in `RUN_COMMANDS.md`.

## Audit and raw retention

Separate network-disabled/read-only Docker auditor returned `PASS_RAW_AUDIT`, zero errors, 18 reconstructed cells, exact A/B, exact support prefixes, deltas `[0.0263671875, 0.043212890625, -0.02001953125]`, positive count 2. The six ~2 MB raw arm JSONs, three per-seed summaries and aggregate summary are retained in the dedicated local Docker volume `unjuno-needle-role-c-support64-replication-4884-v1`, and in the task-local `raw/` export. Docker-volume and local-export SHA-256 values matched file-by-file. Full checksums and sizes: `RAW_MANIFEST.json`.

The full ~12 MB raw JSON set is retained locally with a lossless checksum manifest; GitHub stores the complete per-seed score summary, audit, source, commands and raw SHA-256 manifest. No raw file was truncated or represented as fully uploaded.

## Scope and interpretation

This reproduces a positive support64 effect directionally in two seeds, but one fresh seed reverses it. Support count is inseparable from the treatment by design. One synthetic generator/model family and fixed held-out sets limit transfer. No online real-time learning, concurrency, natural skill transfer, GUI task, integrated runtime, production readiness, or action authority was measured. Do not pool with predecessor #4853's seed or infer broad LoRA efficacy.
