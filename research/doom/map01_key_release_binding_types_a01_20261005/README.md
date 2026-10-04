# Strict scalar and execution context checks for the per-key receipt contract

This construction study checks whether the synthetic v1 reducer distinguishes JSON scalar types and binds admission context to the named execution step.

- **H:** The v1 reducer accepts a malformed step/sequence alias or an admission from a different step, because it uses Python equality/order without exact-type checks or execution-step binding.
- **T:** Run one valid baseline plus five single-fault cases: boolean up step, boolean up sequence, boolean admission sequence, floating release sequence, and admission step outside the execution. Compare the retained v1 reducer to a strict candidate and an independently written oracle.
- **D:** The contract defect is reproduced if v1 accepts any malformed case. The strict candidate passes this scoped construction gate only if it passes the baseline, rejects all five mutations with frozen reasons, and agrees with the independent oracle on every case.
- **C:** These are synthetic JSON receipts and ordering tokens. They do not establish that runtime producers emit these records or that the fields map to physical events.
- **U:** Runtime identity emission, useful feedback, bounded recovery, input timing, model/game behavior, threat response, MAP01 completion, safety, and live efficacy remain untested.

Source: PR #7787 candidate at commit `ac911a4e8b8c377a5b96c8974239c58b02918316`; fixture contract version 1. The first two pytest cases were written first and observed failing because the v1 reducer returned `PASS/complete` for boolean aliases. The strict A01 reducer and oracle preserve that behavior as an explicit v1 counterexample and then test the corrected contract.

Outcome: v1 accepted all five malformed/context-mismatch cases as `PASS/complete`. The strict candidate rejected all five with the frozen reasons; the separate oracle agreed on all six rows. Pinned WSLc candidate, audit and byte-compilation commands exited 0. The WSL host warned that memory is limited without swap. Focused host regression tests passed 5/5. A full repository pytest collection was attempted but stopped with 66 unrelated import/collection errors (including missing/broken `PIL.Image` and paths omitted by the sparse checkout); these do not change the scoped result and remain a repository-environment limitation.

No live allocation, GUI, model, game, or physical input was used.
