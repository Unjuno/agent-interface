# P12 matched direct/compiled caller replication — sanitized result

**Disposition: `PASS_SCOPED_MATCHED_FAKE_X_COMPARISON`.** One preregistered matched pair (two one-shot cells) compared the direct public input route and compiled public caller on child-owned deterministic Fake X. Both used the same public observation image and model-selected point, each produced one owner-side click/effect, the expected pixel, verified release, and a complete reconciled usage ledger. The separate scorer recorded the synthetic task effect; runtime `task_success` remained `null`. Each cell passed 15/15 local audit checks.

## Descriptive pair

| Measure | Direct | Compiled | Direct minus compiled |
|---|---:|---:|---:|
| Provider turn (ms) | 6464.2 | 5345.7 | +1118.6 |
| Observation to action return (ms) | 6731.5 | 5606.4 | +1125.0 |
| Total trial (ms) | 7568.8 | 6255.1 | +1313.7 |
| Input tokens | 10188 | 10194 | -6 |
| Output tokens | 59 | 53 | +6 |
| Reasoning output tokens | 40 | 34 | +6 |
| Public tool calls | 5 | 5 | 0 |
| Compiled transitions | 0 | 1 | — |

The only pair showed the direct route slower on these measured times. Order was fixed (direct then compiled), n=1 per arm, so this does not estimate an effect, reliability or population performance. Image-input token details and upstream billing were unavailable.

## Scope and custody

All 10 runtime source hashes and seven preregistered runner hashes matched. Raw recorder references (9 per cell), provider terminal usage, App Server protocol usage and ledger usage reconciled; the per-cell manifest verified after privacy redaction, with raw `.bin` records left byte-for-byte unchanged. A default Python 3.11.9 preflight stopped before App Server start and before provider generation; a separate input-free preflight on Python 3.13.14 initialized and closed successfully. The model cells then ran on Python 3.13.14.

The full raw packet remains local because immutable provider/MCP `.bin` records may contain local Windows profile paths. This sanitized derivative contains no raw records and cannot independently replay the local raw audit. No WSLc, Docker or physical input was used. This is synthetic Fake X evidence only; it does not qualify live GUI/MAP01 transfer, blocked-I/O recovery or broad reliability.
