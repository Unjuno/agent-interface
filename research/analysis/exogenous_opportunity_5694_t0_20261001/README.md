# Issue #5694 T0

Finite synthetic test of whether completed-cycle latency percentiles can look better while externally scheduled opportunities expire during a controller busy period. This is measurement-method evidence only.

See `PLAN.md` and the pre-run freeze manifest for the exact scenarios, decision rule, hashes, and commands. `runner.py` emits raw event inputs only. `audit.py` independently reconstructs the result without importing the runner. `test_contract.py` includes the intended inversion, no-stall, censoring, overlap, clock, denominator and auditor-integrity controls.

Work ran in Ubuntu WSL2 using CPython 3.12.3 and the standard library. Docker Desktop was not usable from the Windows read-only probe (5-second timeout); its WSL context was unavailable, and the shared OrbStack ownership gate remains unresolved. No Docker/OrbStack container, GUI, user data, model, external service or network was used.

Do not interpret this synthetic result as evidence that any retained/live GUI-agent latency result is biased, that effects can be scored this way in a real application, or that a runtime or product is safer/faster. A live transfer requires a prospectively scheduled exogenous cue source and an independent task-effect oracle.
