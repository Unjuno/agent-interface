# Issue #6138 T0b — reusable-artifact value boundary

## H / T / D / C / U

- **H:** A surviving artifact may rationally change CONTINUE/SWITCH only when independent forward evidence establishes its applicability and consequence. An invalid/stale artifact must not receive that future value. Irrecoverable prior spend alone must not change the choice.
- **T:** Freeze four deterministic recovery cards with exact rational utility: baseline; same forward state with prior spend 200 instead of 2; verified applicable artifact that raises CONTINUE success probability from 1/2 to 9/10; and a present-but-stale artifact whose applicability is false and whose forward success evidence remains 1/2. Compare the baseline to each control and independently reconstruct every value and label.
- **D:** `PASS_METHOD_SCOPED` iff the sunk-only pair is forward-equivalent and selects SWITCH in both; the verified-artifact card is not equivalent and selects CONTINUE (8 > 5); the stale-artifact card is not equivalent because validity differs but still selects SWITCH (4 < 5); raw-only audit reconstructs all cards/pairs and rejects planted result, applicability, and match-label corruptions. Any failure is retained, not tuned/retried.
- **C:** Exact fractions, authored synthetic values, pinned Python image, candidate and independent auditor in separate one-shot OrbStack containers; no network/model/GUI/live action. Build and test locally before freeze; no source edit after freeze.
- **U:** Synthetic decision-oracle boundary only. No claim about real artifact utility, agent/model bias, GUI outcome, task benefit, or production policy. Does not authorize model-facing T1 or change Issue #57 historical evidence.

## Freeze / allocation

- Successor allocation: `HOST-6138-ARTIFACT-VALUE-T0B-20261002-01`.
- Base: current main at intake; source and fixture hashes are recorded in `FREEZE.json` after construction checks and before formal candidate/auditor invocations.
- Formal invocations: exactly one candidate and one independent auditor in separate containers; retries 0. Container/runtime limitation is a STOP, not a scientific result.
