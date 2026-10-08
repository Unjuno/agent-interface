# Formal allocation result — Issue #4813

Allocation: `needle-single-query-ack-6911201-6911301-6911401-v2`.

## Disposition

`HOLD_LATENCY_BUDGET`: integrity passed (72/72 arm-arrivals, zero auditor errors, five corruption controls rejected), and query-only p95 remained under 60 ms on all seeds. The required <=0.5 paired ratio failed on all three: 0.891, 0.930 and 1.199. The data do not support a >=2x acknowledgement-latency improvement.

| Seed | INLINE_512 p95 | ONLINE_QUERY_ONLY p95 | Ratio |
|---:|---:|---:|---:|
| 6911201 | 26.554 ms | 23.655 ms | 0.891 |
| 6911301 | 20.863 ms | 19.406 ms | 0.930 |
| 6911401 | 18.598 ms | 22.291 ms | 1.199 |

## Artifacts and replay

- `FORMAL_RESULT.json`: concise decision and per-seed metrics.
- `FORMAL_ARTIFACT_MANIFEST.json`: original byte sizes and SHA-256 for raw runs, worker inputs, audit and final volume snapshots.
- `audit/AUDIT.json`: frozen independent auditor result.
- `training/<seed>/worker-input.json`: exact trainer worker boundary per seed.
- `training/<seed>/run.parts/part-000.txt` … `part-029.txt`: exact raw run JSON divided into ordered 10,000-character UTF-8 pieces. Concatenate numerically without separators to reconstruct `run.json`; verify byte count and SHA-256 from the manifest. `training/<seed>/run.json` is an explicit pointer, not raw evidence.
- `volume-final/<seed>/<arm>/snapshot.json`: actual final-volume snapshot export; paired arm files hash-identical for every seed.

All 90 raw chunks and 12 ordinary artifacts were read back through GitHub MCP and their blob IDs matched the local bytes. The frozen source/test/baseline hashes are in the parent `FREEZE.json`. The original #4732 STOP and post-hoc HOLD remain unchanged.

## Scope

Synthetic local Docker CPU adapter/ack timing only. No Cactus Needle 3 learning-quality, live Astra, GUI/task success, throughput, production durability or action-authority claim.
