# Verifier Registry T0 v6 (Issue #5273)

This additive package tests **preflight metadata only** against the frozen #5268 Verification IR v0.1 schema. It does not invoke a verifier, dispatch work, schedule dependencies, or grant authority. The five descriptor categories are synthetic placeholders; all cost values are declared fixture estimates, not measurements.

## Reproduce (host construction)

From this directory, with Python 3 and the repository's adjacent verification_ir_5268_v1 path available:

```sh
PYTHONPATH=.. python3 -m unittest -v test_registry test_audit
PYTHONPATH=.. python3 run_host.py
PYTHONPATH=.. python3 audit.py
```

The corpus is frozen in cases.json; do not regenerate it after the freeze. run_host.py reads it and emits raw_host.json without dispatch. audit.py reads only the frozen corpus and raw output, then uses a separate oracle and strict schema checks. The tests also reject altered decisions, input bindings, extra output fields, and mislabeled cost provenance.

## H / T / D / C / U

- **H:** A versioned registry contract lets a preflight reject unsupported/incompatible verifier assignments and infeasible deadlines before any verifier call.
- **T:** Eight frozen #5273 cases: unsupported primitive, wrong input evidence role, stale version, unavailable resource, cold budget violation, warm feasible, prohibited side effect, and deadline infeasible while resources are unavailable. Separate construction tests cover output-role mismatch, unknown/duplicate verifier identity, duplicate/missing/extra assignment coverage, and five descriptor categories.
- **D:** PASS is limited to host construction and independent raw audit: 19 tests pass; eight frozen case outcomes match the separate oracle; zero dispatches. An offline SHA-bound raw record and corruption controls are retained.
- **C:** Frozen source base 1f858cf0d2da2821b5767077e1c9556764507dbb. Cost/latency values and the tick unit are fixture-only. #5085 has no exact named allocation lease for this experiment, and concurrent CPU/container requests exist; container execution is therefore STOP with zero invocations and no Docker/OrbStack command.
- **U:** No operational verifier correctness, measured latency/cost, scheduler benefit, dependency ordering, runtime integration, model/GPU/container behavior, or action authority is established. This does not complete #5273.
