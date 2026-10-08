# Issue #6580 T0c — formal result

Allocation `MODEL-AMBIGUITY-EXHAUSTIVE-6580-T0C-20261002-01` was preregistered on Issue #6580 before any formal invocation. Sources and rules are frozen in [`FREEZE.json`](FREEZE.json) and [`PREREGISTRATION.md`](PREREGISTRATION.md).

## Result

**PASS_METHOD_SCOPED.** Native WSLc 3.0.1.0, cached digest-pinned Python image, network disabled, CPU-only, pull disabled. Construction, candidate generation, and independent audit each ran exactly once; all returned exit code 0. The construction stage passed all five tests, including dropping/inverting an ambiguous theta=1 public branch and mutating a negative-control action.

| Check | Expected | Observed |
|---|---:|---:|
| Scenario keys | 48 | 48 |
| Nature-first public branches | 42 | 42 |
| Agent-first reactive rows | 24 | 24 |
| Total candidate branches | 66 | 66 |
| Negative controls | 6 | 6 |
| Auditor errors | 0 | 0 |

The independent auditor reconstructed all public support values and corresponding A/B choices, confirmed ambiguous agent-first cases yield without action, and checked safe reachable theta for each continuation. It reported 48 safe continuation branches; ambiguous responsive rows remain yields. Candidate output and auditor input copy have matching SHA-256 `7edc1879381f6dc0c8fd57a5b293f8d09e92967afdef2d2c903709fcf556c838`. Auditor JSON is retained at `audit_output/audit.json`.

## Runtime record and limits

WSLc emitted: `Your kernel does not support swap limit capabilities or the cgroup is not mounted. Memory limited without swap.` The command requested `--memory 1G`, but effective memory enforcement is not claimed. No network access, model call, or external effect occurred. Raw output, stdout/stderr, exit receipts, and invocation timestamps are retained under this allocation.

This closes only the representative-value branch-coverage gap in T0b's synthetic finite table. It does not change prior allocations. It provides no evidence about real interface sessions, model lifetime, task success, or product safety. The retained-evidence audit remains `HOLD_MODEL_LIFETIME_UNIDENTIFIED`; T1/T2 remain gated.
