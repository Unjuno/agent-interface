# Authenticated install key-rotation / revocation v1

Task: `COORD-AUTH-KEY-ROTATION-20260917-027`

Decision: **`PASS_AUTH_KEY_EPOCH_REVOCATION_SCOPED`**

## Method

Container-first deterministic state-machine experiment. Authentication semantics from the predecessor are held fixed; the only new factor is trusted-key rotation/revocation semantics. Three Ed25519 keypairs were generated before freeze. Publication retains only public keys, signatures, and canonical fixture data; no private key material is retained.

## First outcome

| Case | Outcome |
|---|---|
| accumulating trust after K1→K2 rotation; old K1 signs I2→I3 | `INSTALLED`; fresh I3 intent `APPLIED` |
| candidate current epoch=2/current signer=K2; old K1/epoch1 | `STALE_INSTALL_KEY_EPOCH`, install writes 0 |
| candidate K2/epoch2 signs exact I2→I3 | `INSTALLED`; fresh I3 intent `APPLIED` once |
| valid K2 signature reused with mutated install content | `INSTALL_SIGNATURE_INVALID`, install writes 0 |
| future key epoch | `FUTURE_INSTALL_KEY_EPOCH` |
| signer-id/public-key mismatch | `INSTALL_SIGNATURE_INVALID` |
| exact signed replay | `ALREADY_INSTALLED_SELF` |
| same install ID with separately valid changed K2 content | `INSTALL_RECEIPT_CONFLICT` |

## Container checks

- `py_compile`: PASS
- unit tests: 10/10 PASS
- formal runner invocations: 1
- formal reruns: 0
- `verify.py`: PASS_VERIFY
- source/fixture SHA-256 recheck: 5/5 PASS
- retained private-key files: 0

## Interpretation

Accumulating trusted keys is rotation without revocation: the old K1 remains capable of minting new installation authority after K2 is introduced. A scalar `current_key_epoch` plus one current signer/public key closes that scoped path while preserving K2 liveness and existing content-bound replay/conflict behavior.

## Boundary

Key-epoch activation is fixture-authored and trusted. This does not establish durable/authenticated key rotation itself, revocation distribution, HSM custody, malicious current-signer resistance, crash/power-loss durability, distributed election, external-effect safety, or production exactly-once semantics.

## Next question

Keep install verification and current-key-epoch semantics fixed. Make the key-epoch rotation itself a durable/authenticated state transition, then test rollback or forged rotation-state changes.
