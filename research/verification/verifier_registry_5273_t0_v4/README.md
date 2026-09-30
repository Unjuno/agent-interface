# Issue #5273 verifier-registry T0 v4

## H / T / D / C / U

- **H:** A registry preflight can determine compatibility for every #5268 verification-IR check from the exact IR, verifier assignment, registry snapshot and resource snapshot, while dispatching nothing and granting no authority. Hard incompatibility must remain `REJECTED` even when resources are unavailable.
- **T:** A frozen four-case construction corpus covers compatible assignment, stale verifier with unavailable resources, unknown verifier, and a two-check IR whose dependency metadata is preserved. Python host execution only; no container, model, GUI, GPU, or dispatch.
- **D:** `PASS_HOST_CONSTRUCTION_ONLY`: 11/11 host unit tests pass; one runner invocation produced four rows, zero dispatches; the independent raw-only auditor recomputed all four exactly. This is a small synthetic construction result, not an operational or scientific result.
- **C:** `FREEZE.json` pins source/input hashes. `RAW.json` contains each complete IR/assignment/registry/resource input and observed output. `AUDIT.json` binds raw rows to frozen cases and independently recomputes each decision. Corruption controls reject changed assignment inputs and extra observed fields.
- **U:** No container lease was available under #5085. No Docker/OrbStack command was run. Dependency metadata is retained but no scheduling/order semantics are tested. No verifier was invoked; no runtime, safety, latency, model-quality, or product claim follows. The PR is Draft; v1-v3 remain immutable and unmerged.

## Reproduction

From this directory, with Python 3 and repository root on `PYTHONPATH`:

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.. python3 -S -B -m unittest -v test_registry test_audit
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.. python3 -S -B run_host.py
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.. python3 -S -B -c 'from audit import audit_file; print(audit_file("RAW.json", "cases.json"))'
```

`run_host.py` is a one-shot evidence writer. Do not rerun it as a substitute for a separately authorized allocation. The dependency case checks only that the parent IR can carry a dependency edge; this package does not interpret that edge as an execution constraint.
