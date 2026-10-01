# Layered lifetime admission contract — R0 retained result

Issue #1678.

## Decision

**PASS_LAYERED_LIFETIME_ADMISSION_CONTRACT_SCOPED**

With a declared dependency mask, checking independent layer epochs exactly matches the currentness oracle across every non-empty dependency mask and every changed-layer subset.

## Formal corpus

Five layers:
- binding
- precondition
- route
- observation_cache
- motor_calibration

31 non-empty dependency masks × 32 change masks = **992** exhaustive rows.

| Policy | stale accepts | false invalidations |
|---|---:|---:|
| LAYERED_EPOCHS | **0** | **0** |
| GLOBAL_EPOCH | 0 | **180** |
| ROUTE_ONLY_EPOCH | **350** | **65** |

Candidate/oracle mismatch: **0**.

All five one-layer directed controls admit when unchanged and reject when that same layer changes.

## Interpretation

A global epoch can remain safe by invalidating everything, but that destroys the project's narrow-invalidation objective when unrelated state changes. A route-only epoch is neither complete nor narrow: non-route dependency changes can escape admission, while route changes can invalidate a token that did not depend on route.

The scoped contract is therefore:

> bind reusable evidence/program tokens to the exact declared lifetime identities they depend on, and admit only when every bound identity is current.

This does not require five literal counters in a production ABI. Layers that are independently proven to share a lifetime may share one epoch/token. Conversely, collapsing independently changing layers without an explicit dependency contract either gives up reuse or risks stale admission.

## Integrity

Remote source readback before formal:
- formal.py Git blob `6204a14e8c61fee9530998e74eda7c9353fbd027`
- audit.py Git blob `4ceb163449b6bc505644d4284462d0c518324056`

Local `git hash-object` matched both exactly before formal1.

One formal invocation; reruns/replacements/tuning0. Independent audit PASS/errors[]; six corruption controls reject.

## Boundary

Dependency masks are assumed correct. #165 owns dependency discovery. This result does not measure natural invalidation rates, runtime overhead/speed, task correctness, model boundaries or production ABI. The next high-information rung is a composed real/retained path in which one layer changes while an unrelated reusable layer remains valid.
