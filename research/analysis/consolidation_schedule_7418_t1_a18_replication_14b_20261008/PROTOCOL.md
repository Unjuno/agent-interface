# T1-A18 protocol: independent-seed replication

## Question
Does A16's clean transition audit and scoped schedule-sensitivity pattern recur under the same Qwen3 14B configuration when only the numeric seeds are replaced with a fresh preregistered set?

## Allocation
- ID: `GUI-MEMORY-CONSOLIDATION-SCHEDULE-8406-T1-A18-REPLICATION-14B-20261008`.
- Fresh seeds: 5701, 5702, 5703; four schedules; six checkpoints; five held-out queries.
- 360 query calls plus 30 consolidation calls = 390.
- Model: `qwen3:14b`, 14.8B parameters, Q4_K_M; frozen digest `bdbd181c33f2ed1b31c972991882db3cf4d192569092138a7d29e973cd9debe8`.
- Existing private model store: `/tmp/unjuno-8406-t1-a16-ollama-store`; isolated server at `127.0.0.1:11435`. The store is reused read-only; no model download is planned.

## Single intervention and controls
Relative to A16, only the seed values change. Model digest, prompt/schema, immutable episode ledger and order, queries/oracle, four schedule arms, decoding, candidate, independent transition auditor, call allocation, and per-checkpoint scoring remain byte-identical. A17's separate 8B failed-audit outputs are not used or pooled. This is a repeatability check, not an independent corpus or model-family validation.

## Execution and interpretation
1. Freeze and preregister the candidate, audit, query, fixture, and scoring inputs before model generation.
2. Run the read-only private-tag and every-manifest-layer preflight; stop on any identity or file mismatch.
3. Invoke the candidate once. Do not retry, replace seeds, repair outputs, or pool with A16/A17.
4. If all 390 rows complete without call errors, run the independent auditor once.
5. Preserve raw, audit, reconstructed checkpoint metrics and checksums; stop the isolated server.

Any candidate call error, interruption, identity change, or incomplete row count is `STOP/INCOMPLETE`. Any transition-audit error is `FAIL_METHOD`; schedule accuracy remains descriptive only. Only `PASS_METHOD` permits schedule comparisons, and only `PASS_CADENCE_SENSITIVITY_SCOPED` under the inherited consistent >=0.10 contrast rule permits the scoped cadence-sensitivity statement. A pass remains limited to this synthetic fixture and the tested Qwen3 14B configuration. No GUI, product, action-effect, or universal cadence claim is authorized by this experiment.
