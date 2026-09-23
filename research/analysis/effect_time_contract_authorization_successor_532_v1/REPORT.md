# Issue #2072 successor — effect-time contract authorization

## H/T/D/C/U

- **H:** A consequential effect contract is admissible only when issuer, scope, target/session, epoch, expiry, and receipt signature match the authorized context; later generations cannot rewrite the frozen effect-time evaluation.
- **T:** Freeze authorized, unauthorized, wrong-scope, wrong-target, expired, and malformed generations; verify effect-time evaluation remains bound to the admitted generation.
- **D:** experiment.py, six admission rows, frozen-generation check, authority counter, and SHA-256 digest.
- **C:** Only the authorized matching generation is admitted; all invalid controls fail closed; later generation does not rewrite the historical value; authority promotions remain zero.
- **U:** Cryptographic implementation, issuer lifecycle, real application semantics, latency, liveness, model use, and runtime integration remain unknown.
- **STOP:** One finite standard-library contract fixture; no model, GUI, network, runtime, or input action.

## Result

Command: python experiment.py

- Authorized matching generation: admitted.
- Unauthorized, wrong scope, wrong target, expired, malformed: rejected.
- Later generation cannot rewrite the frozen effect-time value.
- Authority promotions: 0.
- Digest: 7ec122095be2da7c780e56f10c4bb3276d09e30216f114b7a3782ee83fd3e636.

**Decision: PASS_EFFECT_TIME_CONTRACT_AUTHORIZATION_SCOPED.**

This verifies only finite admission and temporal-binding behavior. It does not establish cryptographic implementation, issuer lifecycle, real application semantics, liveness, model use, or runtime integration.
