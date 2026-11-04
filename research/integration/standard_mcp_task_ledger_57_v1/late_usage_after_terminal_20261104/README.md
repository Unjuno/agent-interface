# Late provider usage after a terminal timeout

## Question and decision

Can a locally recorded provider usage receipt arrive after the caller has already received a timeout and after an independent task score has been recorded, without reopening the attempt, changing its terminal status or task score, or counting the attempt twice?

The current-main recorder had no append-only path for a post-terminal usage receipt. This successor adds one accounting-only observation type. A receipt is explicitly a cumulative `attempt_total`, is raw-byte retained and SHA-256 checked, and is joined to the original attempt. It does not represent a real provider delivery or billing guarantee.

## Frozen conditions

- Source baseline: `6d48883bac760d6ec5406e1c7adb7884d94a1f03` (current `origin/main` at start).
- Platform/runtime: Windows, Python 3.11.9; no Docker, model provider, GUI, or live allocation used.
- Synthetic attempt: attempt `attempt-01` starts at monotonic 10, caller timeout terminal at 20, independent score at 30, first partial receipt at 35, and complete receipt at 40.
- The first cumulative receipt reports 17 input tokens and unknown output. A rejected regression tries 16 input tokens. The final receipt reports 17 input and 3 output. Reconciliation retains both valid raw receipts and projects only the final total onto the same attempt.
- Assertions require status `timeout`, unchanged successful task score, one provider attempt, totals 17/3 once, raw receipt hash/reference integrity, late-time and counter-regression rejection, post-completion update rejection, and refusal of a new attempt after scoring. Journal mutation controls reject boolean and float observation indexes.
- Composition regression: existing Fake X public MCP endpoint suite exercises caller/tool behavior without changing its fixtures or expected effects.

## Results

| Check | Normal | Optimized (`-O`) |
|---|---:|---:|
| ProviderAttemptRecorder | 19/19 PASS | 19/19 PASS |
| Recorded usage bridge | 3/3 PASS | 3/3 PASS |
| Public Fake X MCP composition | 17/17 PASS | 17/17 PASS |

Exact stdout/stderr and exit codes are in the adjacent `.log` and `.exit_code.txt` files. Result acceptance requires every command to exit 0.

## Scope

This establishes the local append-only ledger behavior only. It does not show that a provider sends usage after timeout, that provider usage counters mean cumulative attempt totals, that billing is complete, or that any production caller currently invokes `observe_late_usage`. Issue #57's integrated live-provider accounting, matched economics, WSLc and MAP01 gates remain open.
