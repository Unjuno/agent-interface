# P13 reversed-order matched caller replication — sanitized result

**Disposition: `PASS_SCOPED_MATCHED_FAKE_X_COMPARISON`.** One preregistered pair ran the compiled caller first, then direct public input, on child-owned deterministic Fake X. Both cells passed 15/15 audit checks. Each selected the same point from the exact public observation, minted on that sequence, produced one independently scored synthetic click/effect and expected pixel, and verified release. Provider/App Server/ledger usage reconciled; runtime `task_success` remained `null`.

| Measure | Direct | Compiled | Direct minus compiled |
|---|---:|---:|---:|
| Provider turn (ms) | 10143.0 | 11179.8 | -1036.7 |
| Observation to action return (ms) | 10389.5 | 11446.1 | -1056.6 |
| Total trial (ms) | 11184.9 | 12087.4 | -902.5 |
| Input tokens | 10188 | 10194 | -6 |
| Output tokens | 117 | 76 | +41 |
| Reasoning output tokens | 98 | 57 | +41 |
| Public tool calls | 5 | 5 | 0 |
| Compiled transitions | 0 | 1 | — |

The reversed-order P13 pair showed the opposite latency direction from the direct-first P12 pair. Across the two pairs, the median direct-minus-compiled deltas were **+40.9 ms** per provider turn, **+34.2 ms** to action return, and **+205.6 ms** total. Token deltas were −6 input, +23.5 output and +23.5 reasoning tokens. These two pairs are descriptive only and do not support a causal comparison or reliability estimate.

## Scope and custody

All 10 preregistered runtime source hashes and seven runner hashes matched. Raw ledger references, provider result, App Server protocol usage and ledger totals reconciled; per-cell hash manifests passed and raw `.bin` files were not redacted. The full raw packet remains local-only because immutable records may contain local Windows profile paths. This sanitized derivative excludes raw and cannot independently replay the local audits. No WSLc, Docker or physical input was used. No live GUI/MAP01, blocked-I/O recovery, image-token accounting or broad reliability is established.
