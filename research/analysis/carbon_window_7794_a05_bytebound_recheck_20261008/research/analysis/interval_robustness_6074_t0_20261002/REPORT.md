# Issue #6074 T0 — interval robustness finite-method probe

## Disposition

`METHOD_PASS_SCOPED` from one frozen local execution and a separately coded finite endpoint oracle. Candidate and oracle agreed on all nine cases: clear interior → `ROBUST_TRUE_SCOPED`; clear exterior → `ROBUST_FALSE_SCOPED`; threshold-straddling, exact zero margin, near-deadline, possible between-sample short crossing without a rate bound, overlapping timestamp intervals, missing coverage, and wrong identity binding → `UNKNOWN`. Three fail-closed mutations (widen interval, remove identity, remove coverage) remained UNKNOWN. No robust label was produced from an unsupported continuous-time or identity claim.

The result is finite synthetic arithmetic evidence only. It does not validate GUI error calibration, a temporal monitor implementation, sampled-to-continuous inference, semantic target identity, authority, runtime integration, or task benefit. T1 remains conditional and unrun.

## H / T / D / C / U

See frozen `PLAN.md`. No model, GUI, user input, formal/live allocation, or external service was used. The candidate, independent oracle, raw outputs, audit, and source hashes are retained here.

## Execution environment

`Docker Desktop` processes were present and responsive, but `docker --context desktop-linux version --format 'client={{.Client.Version}} server={{.Server.Version}}'` produced no response and had to be interrupted. The frozen candidate/audit therefore ran once with local Python 3.12.10; Docker was not used and no container result is claimed. This is a retained infrastructure limitation, not a candidate retry.
