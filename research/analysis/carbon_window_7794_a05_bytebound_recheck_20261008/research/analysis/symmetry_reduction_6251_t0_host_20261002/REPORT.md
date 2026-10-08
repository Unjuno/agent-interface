# Issue #6251 T0 result — host-only, method-scoped

## Disposition

`PASS_METHOD_SCOPED`. The preregistered candidate and separately implemented auditor each ran once, with zero retries. This is a bounded synthetic transition-system result on the Windows host; it is not a Docker/container, production-runtime, live-interface, or general symmetry proof.

## Recorded execution

- Allocation: `PROPERTY-SYMMETRY-REDUCTION-6251-T0-HOST-20261002-01`.
- Freeze commit: `926fe22` (base `97afcb82f90616589801a256893f886010ed6d27`).
- Environment: Windows 11 x64 build 26200; CPython 3.12.10; stdlib only; network/model/GUI unused. Docker service was stopped and shared slot unassigned; no Docker state was changed.
- Construction: `python -B -m unittest discover -s research/analysis/symmetry_reduction_6251_t0_host_20261002 -p 'test_*.py' -v` — PASS, 8/8.
- Candidate: `python -B research/analysis/symmetry_reduction_6251_t0_host_20261002/candidate.py --output research/analysis/symmetry_reduction_6251_t0_host_20261002/candidate.raw.json` — exit 0; one invocation.
- Independent auditor: `python -B research/analysis/symmetry_reduction_6251_t0_host_20261002/audit.py research/analysis/symmetry_reduction_6251_t0_host_20261002/candidate.raw.json --output research/analysis/symmetry_reduction_6251_t0_host_20261002/audit.raw.json` — exit 0; `PASS_METHOD_SCOPED`, no errors; one invocation.

## Results

- Named reachable states: 312; typed verifier-swap quotient classes: 166 (strict reduction of 146 classes, 46.8%).
- Transition checks: 624; equivariance held. Property checks: 624; invariance held.
- Unsafe states retained: 272 named and 144 quotient classes; unsafe existence held in both. All quotient counterexample witnesses expanded/replayed.
- Naive all-actor-ID quotient produced 32 property-mismatched classes and lost a property distinction, so it is rejected.
- All four controls were rejected/fell back to named states: verifier-specific owner, identity-bound lease holder, verifier-named property, and omitted effect-target key. Counterexample expansion held for every control.
- Auditor reconstructed the result independently and accepted it with an empty error list.

## Artifacts / integrity

- `candidate.raw.json`: 2,600,142 bytes; SHA-256 `56D9D38F65DC91F4092B947E399BB2669744D449AD5975DB64F354F2B30D15E2`.
- `audit.raw.json`: 109 bytes; SHA-256 `C18B896A4B40850093FFD5647BC8F6CDE1348620B095A3903B28BF4E924AED29`.
- Source and preregistration hashes are recorded in `FREEZE.json`; all result-file hashes are in `SHA256SUMS`.

## Limits

Only the finite model and explicitly encoded identity-breaking controls were tested. Hidden actor-specific state, dynamic membership, fairness/liveness, real external effects, runtime authority, partial-order reduction, production safety, GUI behavior, container reproducibility, and generalization to other systems remain unverified. Preserve this report as a method-scoped result; it does not supersede earlier Issue #6251 evidence.
