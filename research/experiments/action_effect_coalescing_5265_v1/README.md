# Issue #5265 experiment package

This additive package tests whether a finite authority-neutral proposal matrix can distinguish semantic duplicate effects from legitimate later actions. It is separate from runtime implementation and from #24's transport/idempotency contract.

- Preregistered H/T/D/C/U: [`PLAN.md`](PLAN.md)
- Exact source and input identity / one-shot commands: [`FREEZE.json`](FREEZE.json)
- Pre-freeze construction attempts, including the preserved launcher failure: [`CONSTRUCTION.md`](CONSTRUCTION.md)
- Frozen inputs: [`workload.json`](workload.json)
- Candidate state machine: [`experiment.py`](experiment.py)
- Independent oracle and raw auditor: [`oracle.py`](oracle.py), [`audit.py`](audit.py)
- Construction and mutation tests: `test_coalescing.py`, `test_audit.py`
- Formal and audit records: `results/formal-01/` (created only after the frozen invocations)

The planned output is a synthetic protocol observation only. It grants no action authority and makes no application-effect claim.
