# Result: raw replay receipts reproduced

Disposition: **`PASS_RAW_RECEIPT_REPRODUCED`**, method/provenance scope only. Candidate invocations: 2 total (one per trace). Independent raw-only auditor: 1. Retries/substitutions: 0. No container, model, network call, GUI/game input, or external task effect was used.

| Trace | Completed holds | Verified interruption | Requested | Owner-commanded interval bound | Overshoot fraction |
|---|---:|---:|---:|---:|---:|
| v38 | 11 | 0 | 3,600 ms | 4,233.848798–4,377.563483 ms | 17.6069%–21.5989856% |
| v39 | 27 | 1 | 8,930 ms | 10,544.034974–10,873.310311 ms | 18.0742998%–21.7615936% |

The raw-only reconstruction matched every candidate row, all aggregate fields, and all limitation fields for both traces. The single v39 interrupted row retained its verified-empty boundary (212.579736 ms from the full-keyset acknowledgment). Independent-auditor controls rejected an omitted completed row, a modified acknowledgment timestamp, and a modified completed-row count (12/12 checks overall).

This fills the receipt gap for a replay of the exact historical analyzer and logs. It does not retroactively turn #6175's original missing receipts into retained raw output, and it does not create new experimental observations. Physical keymap occupancy, useful-feedback onset, causality, live safety, game success, or product benefit remain unestablished. See `PLAN.md` for H/T/D/C/U and `FREEZE.json` for exact source/input identities and commands.
