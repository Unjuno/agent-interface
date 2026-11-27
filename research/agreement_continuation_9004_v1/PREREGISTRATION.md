# Issue #9004 T0 preregistration

Allocation: `9004-agreement-continuation-t0-a01-20261017`  
Scope: finite deterministic CPU simulation only. No GUI, live application, model, network, GPU, or physical input.  
Source base: current main `1ece47014d05db898bf73afcd722a14524462e15`.

## Question and arms

Does exact same-state agreement allow a bounded local controller to continue while a supervisor is delayed, while preserving the independently supplied task-effect truth and release obligation? Compare always-wait, System-1-only, agreement-only at the decision point, and agreement-conditioned lease continuation on the ten fixed cases in `cases.json`.

The candidate is `run_candidate.py`; independent raw-only reconstruction is `audit_raw.py`. The auditor must reconstruct every case/arm transition and reject missing or duplicate rows, unsafe effects, missing release obligations, or scope drift. `test_audit_raw.py` contains preregistered mutation controls. Outcomes are method-scoped only; synthetic ticks cannot support a latency or product claim.

## Frozen gates

Method PASS requires all 40 case/arm rows, exact reconstruction by the independent auditor, zero admitted action contrary to the independent truth, explicit release obligation on every row, and rejection of the four mutation classes. Any discrepancy is FAIL_METHOD. Missing/incomplete source, raw, or custody is HOLD. An execution failure after start consumes this allocation; do not retry it.

H is not evaluated as a speed claim in this allocation. Any measured tick gap is descriptive synthetic bookkeeping only. `formal_pass` remains false regardless of method PASS.
