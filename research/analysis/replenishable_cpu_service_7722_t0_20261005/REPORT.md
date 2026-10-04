# Result — Issue #7722 T0

**Disposition:** `METHOD_PASS_SCOPED`; `FAIL_HYPOTHESIS`.

The bounded audit reconstructed 9,438 one-tick service events across all 18 case/policy runs. It found no integrity, service-accounting, total-budget, class-budget, job-obligation, or reported-outcome error. Each of six mutation controls was rejected: budget, deadline, lost obligation, early replenishment/double charge, uncharged execution, and false completion.

| Fixed-seed schedulable trace | Shared priority p99 (ticks) | Reserved p99 (ticks) | p99 reduction | Shared misses | Reserved misses | BE completions shared → reserved | BE loss |
|---|---:|---:|---:|---:|---:|---:|---:|
| seed 7722 | 584 | 166 | 71.6% | 10 | 3 | 192 → 190 | 1.04% |
| seed 7723 | 586 | 168 | 71.3% | 10 | 2 | 192 → 190 | 1.04% |
| seed 7724 | 561 | 131 | 76.6% | 10 | 1 | 192 → 190 | 1.04% |

The 64-entry backpressure policy matched shared priority in these traces because the frozen queue bound never activated. The negative no-contention trace had p99=4 ticks and zero deadline misses for both shared and reserved policies. The overload and replenishment-boundary cases reported `UNKNOWN_OVERLOAD` for reserved service, retained both control obligations in each case, and recorded the expected deadline miss.

The reserved policy met the p99 and best-effort-loss thresholds, but it did not eliminate baseline deadline misses on any schedulable sensitivity trace. The hypothesis therefore fails as preregistered. In the retained traces, some next-period control jobs arrive before the prior 5-tick server budget has fully replenished; the server dispatches available budget and then delays the remainder past the 100-tick deadline. The data support only this interpretation of the frozen model.

## Scope

This is deterministic synthetic CPU scheduling arithmetic, not a WSL/Linux real-time guarantee. `--cpus 1` and `--memory 256m` were requests. Both container runs emitted: `Your kernel does not support swap limit capabilities or the cgroup is not mounted. Memory limited without swap.` Effective memory/swap enforcement was not verified. CPU enforcement was not independently measured. No GUI, model, host scheduler, input, GPU, memory pressure, production priority change, or physical release was exercised. This does not explain real Issue #59 latency or certify key neutralization.

Do not tune these consumed traces. Any next allocation must freeze a new question and arrival envelope, and must not promote this result to an OS or product claim.
