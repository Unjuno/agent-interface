# Issue #2078 successor — independent effect evidence

## H/T/D/C/U

- **H:** An independent application/effect evidence root can distinguish trusted scorer receipts from forged or contradictory receipts without granting receipt authority.
- **T:** Freeze legitimate, forged effect ID, wrong application effect, missing evidence, and wrong-target traces. Compare typed verifier outcomes.
- **D:** experiment.py, five paired traces, typed outcomes, authority counter, and SHA-256 digest.
- **C:** Legitimate receipt is ACCEPTED; forged/wrong-target receipts are REJECTED; contradictory effect is CONFLICT; missing evidence is UNKNOWN; authority promotions remain zero.
- **U:** Cryptographic root implementation, real application causality, latency, liveness, model use, and runtime integration remain unknown.
- **STOP:** One finite standard-library trust-boundary fixture; no model, GUI, network, runtime, or user input.

## Result

Command: python experiment.py

- Legitimate paired receipt: ACCEPTED.
- Forged effect identity and wrong target: REJECTED.
- Contradictory application effect: CONFLICT.
- Missing independent evidence: UNKNOWN.
- Authority promotions: 0.
- Digest: 146052737362bed5cf68c5dd87cdf27ac09ab0de6a9b37d55a5352d397b2d735.

**Decision: PASS_INDEPENDENT_EFFECT_EVIDENCE_BOUNDARY_SCOPED.**

This verifies only typed trust-boundary behavior. It does not establish cryptographic implementation, real application causality, liveness, latency, model use, or runtime integration.
