# Issue #8623 T0 A01 — evidence-readiness and epistemic-action benchmark

**Allocation:** `EPISTEMIC-ACTION-8623-T0-A01-20261008`  
**Base:** `main` at `f99ac0d3ad084c244cc7558d2219ac87247ded0c`  
**Execution:** local CPython standard-library CPU fixture; no model, GUI, OS input, Docker, WSLc, network, or external state.

## H / T / D / C / U

- **H:** On the preregistered finite cases, the `AVAILABLE` policy improves correct final decisions over `NO_EPISTEMIC_ACTION` on the three evidence-needed cases (missing fact, unusable representation, safe discriminating probe), while the competency ledger exposes at least one stopping defect hidden by aggregate task success. No hard authority, provenance, or unsafe-probe gate may be violated.
- **T:** Six deterministic cases; run `PRESCRIBED`, `AVAILABLE`, and `NO_EPISTEMIC_ACTION` arms with identical final decision options. Record evidence-need recognition, action type, evidence production/provenance, evidence use, stopping, task outcome, and hard-gate violations independently. A raw-only auditor reconstructs every row. Apply four controls: irrelevant probe side effect, lossy transform, fabricated provenance, and unnecessary probe where further evidence cannot change the admissible decision.
- **D:** `PASS_METHOD_SCOPED` only if the independent auditor reconstructs all 18 arm/case rows, every action transition and provenance receipt, and rejects all four mutations. `H_PASS_SCOPED` only if AVAILABLE beats NO_EPISTEMIC_ACTION on all three predeclared evidence-needed cases, uses produced evidence correctly, has zero hard-gate violations, and the stopping error is visible in its competency metric although aggregate task success remains unchanged. Otherwise retain the exact FAIL/HOLD boundary.
- **C:** Authored action costs, evidence states, and deterministic policies may make the distinction easier than real agent decisions. The taxonomy may add no diagnostic value beyond direct task outcomes.
- **U:** Synthetic method evidence only; no model-competence, live-GUI, user-benefit, privacy, deployed-safety, runtime, latency, or product claim. No real epistemic action is authorized.

## Freeze and execution sequence

The fixture, oracle, construction tests, and this plan are frozen before implementation. Tests must show RED against absent candidate/auditor CLIs, then GREEN after implementation. Construction invocations are not formal invocations. After candidate and auditor sources are frozen and hashed, run each official CLI exactly once, retain exact stdout/stderr/exit receipts, and do not retry. The auditor may read fixture/oracle/raw bytes but must not import candidate code.

