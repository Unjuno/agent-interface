# Issue #5273 T0 v5 — deadline/resource precedence successor

## H / T / D / C / U

- **H:** A deadline-infeasible assignment must be classified as `REJECTED` even when current resources are unavailable; a feasible assignment with only temporary resource unavailability must remain `UNAVAILABLE`.
- **T:** Seven frozen #5268 IR v0.1 construction cases cover warm feasible, deadline-infeasible plus resources down, resources-only unavailable, hard primitive incompatibility, stale verifier, wrong output role, and requested-version mismatch. The deadline budget and estimated cost are synthetic same-unit fixture values; no clock or latency is measured.
- **D:** `PASS_HOST_CONSTRUCTION_ONLY`: TDD first observed the missing-preflight RED; final host suite passes 9/9. One frozen host run emits seven decisions with zero dispatches; an independent oracle audits all seven raw rows. Container formal run is `STOP_NO_EXACT_RESOURCE_LEASE`, invocations=0.
- **C:** Freeze pins candidate, literal tests, corpus, oracle, auditor, runner and parent IR validator. Raw contains full IR/assignment/registry/resource inputs and outputs. The auditor never imports the candidate and rejects changed raw assignment inputs and changed decisions.
- **U:** This resolves only decision precedence for the declared fixtures. It does not qualify production registry costs, deadline units, verifier behavior, scheduling, dependency ordering, task correctness, latency, runtime integration or the full #5273 heterogeneous registry. No Docker/OrbStack commands, model, GUI, network, GPU or verifier dispatch were used.

## Reproduction

Run from this directory:

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.. python3 -S -B -m unittest -v test_precedence test_audit
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.. python3 -S -B run_host.py
```

The runner is a one-shot evidence writer. Do not rerun it as a substitute for a newly authorized allocation.
