# Durable incarnation-install receipt v2

Task: `COORD-DURABLE-INCARNATION-INSTALL-20260917-025`

Decision: **`PASS_DURABLE_INCARNATION_INSTALL_RECEIPT_SCOPED`**

Fresh successor to A1 task `...-024`, whose failed first outcome is retained separately. A2 changed only the restart-local diagnostic counter gate from inherited-count `4` to local post-restart count `1`; `model.py` and `test_model.py` are byte-identical to A1.

## First outcome

| Case | Outcome |
|---|---|
| mutable-only I2 install, then mutable state rollback to I1, replay old I1/A/seq1 as g4->g5 | `NEW_INTENT_ALLOWED` -> `APPLIED`, final g5 |
| durable receipt I1->I2 survives mutable rollback to I1 | `INSTALL_STATE_ROLLBACK`; replay transition writes 0; generation stays g4 |
| restart from durable I2 receipt | old I1 -> `STALE_ISSUER_INCARNATION`; fresh I2/A/seq1 -> `NEW_INTENT_ALLOWED` -> `APPLIED` once, final g5 |
| same `install-I2` with changed content I1->I3 | `INSTALL_RECEIPT_CONFLICT` |

## Container checks

- `py_compile`: PASS
- unit tests: 8/8 PASS
- formal runner invocation count: 1
- `verify.py`: `PASS_VERIFY`
- formal reruns: 0
- post-result source hash recheck: 4/4 PASS

## Interpretation

Incarnation-bound intent identity is not sufficient if installation state itself can roll back independently of the already-durable generation. A single content-bound durable installation receipt can act as the recovery authority for the latest installed incarnation in this fixture: mutable rollback is detected before intent admission, and restart can reconstruct I2 while allowing fresh I2 sequence space.

This rung intentionally trusts the install-receipt producer. It establishes durability/content-binding behavior only, not cryptographic authentication.

## Boundary

Deterministic single-process container fixture. No fsync/power-loss proof, malicious signer, distributed election, simultaneous linearizability, external effect or production exactly-once claim.

## Next question

Hold rollback/recovery semantics fixed and authenticate the exact install receipt. Compare caller-forged installation content against a verifier-bound trusted signing identity without adding another state-machine factor.
