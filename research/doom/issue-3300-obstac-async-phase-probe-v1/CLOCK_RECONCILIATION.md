# Async-clock reconciliation for #3456 construction probe

Status: `PASS_CONSTRUCTION_PROBE_SCOPED` remains valid only for calling the frozen scorer, retaining getter brackets, and reproducing its same-tic decision. The separate claim that the probe sampled an **advancing** async episode is not supported by its retained raw trace: `HOLD_ASYNC_CLOCK_PROGRESS_UNVERIFIED`.

This is an additive correction. It does not edit or replace `RESULT.md`, `raw.jsonl`, the original #3300 evidence, or any prior disposition.

## H / question

Did the #3456 construction probe empirically demonstrate that the configured ViZDoom async episode was advancing during scorer measurements?

## T / re-audit

Re-read the runner and raw artifact committed by PR #3456 (head `c05dc3487d46c51dd068423504d351b04108454f`) after it merged as commit `1939ca15674072a91deb905c9df26676aae556b2`. Independently parsed all 36 JSONL rows and recomputed per-stratum timing spans, all 216 logged `get_episode_time()` values, and each row's `final_tic`. No container rerun or replacement allocation was made.

Raw artifact SHA-256 recomputed locally: `bfa27da03e259af1c48da367cd688e301c932abf27263ce10345282a50d02b33`.

| Stratum | Rows | Scorer calls | Tic reads | Read/final tic range | First-to-last recorded span |
|---|---:|---:|---:|---:|---:|
| idle | 12 | 36 | 72 | 14–14 | 2.48 ms |
| CPU load | 12 | 36 | 72 | 14–14 | 496.99 ms |
| delayed read | 12 | 36 | 72 | 14–14 | 837.89 ms |

The runner calls `set_mode(ASYNC_PLAYER)` and `set_ticrate(35)`, but it does not retain `get_mode()` or establish a positive tic rate. Every getter and final tic in the persisted trace equals 14, including across the two long strata. The existing audit checks row/call shape, getter pairing/order, and whether the scorer's same-tic decision agrees with raw reads; it has no advancing-clock gate.

ViZDoom documents that ASYNC modes progress at constant speed without waiting for agent actions ([mode documentation](https://vizdoom.farama.org/api/cpp/enums/)). The retained trace therefore fails to verify the condition “advancing episode”; this may be a setup/runtime issue or an unobserved clock, and the current data do not identify which.

## D / disposition

- Preserve the original `PASS_CONSTRUCTION_PROBE_SCOPED` narrowly: the scorer proxy was callable and the independent same-tic audit agreed for 108 calls.
- Record `HOLD_ASYNC_CLOCK_PROGRESS_UNVERIFIED` for any claim about live async progress, scheduler phase, or real-clock scorer reliability.
- Do not pool these rows into #3300's formal allocation and do not infer the clock was advancing from the configured mode alone.

## C / scope

This audit only reconciles the #3456 construction artifact. It is not a formal phase/load allocation, a gameplay result, a ViZDoom failure finding, or evidence that async mode itself is defective.

## U / next evidence

Before a new formal freeze, require the runner to record the mode readback and episode tic/time at both ends of each timed block, enforce a preregistered positive advancement/tic-rate gate during each intended async interval, and stop setup with an explicit HOLD if that gate fails. Then independently audit this gate on excluded construction data; keep the formal phase schedule, scorer predicate, and one-shot allocation separate under #3453.