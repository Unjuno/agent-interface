# Authenticated incarnation-install receipt v1

Task: `COORD-AUTH-INCARNATION-INSTALL-20260917-026`

Decision: **`PASS_AUTHENTICATED_INCARNATION_INSTALL_RECEIPT_SCOPED`**

## Container-first method

The measured state machine ran in an isolated container. Ed25519 trusted/untrusted keypairs were generated before freeze; private keys were used only to create fixed signed fixtures and were deleted before source/fixture freeze and formal execution. Publication retains only public keys, signatures, canonical receipt data, source, logs, and result.

Checks:
- `py_compile`: PASS
- deterministic unit tests: 9/9 PASS
- formal runner invocations: 1
- `verify.py`: `PASS_VERIFY`
- source/fixture post-result SHA-256 recheck: 5/5 PASS
- formal reruns: 0

## First outcome

| Case | Outcome |
|---|---|
| unauthenticated caller-authored I1->I2 install | `INSTALLED`; fresh I2 intent `APPLIED`, final g5 |
| trusted exact Ed25519-signed I1->I2 install | `INSTALLED`; fresh I2 intent `APPLIED` once |
| valid signature reused with mutated signed content | `INSTALL_SIGNATURE_INVALID`; install writes 0 |
| exact content signed by untrusted signer | `UNTRUSTED_INSTALL_SIGNER`; install writes 0 |
| restart from durable trusted signed receipt | reconstructs I2; old I1 stale; fresh I2 applies |
| exact signed receipt replay | `ALREADY_INSTALLED_SELF` |
| same install ID with separately valid changed trusted content | `INSTALL_RECEIPT_CONFLICT` |

## Interpretation

Durability/content binding alone does not establish who is allowed to create an incarnation-install receipt. In the baseline, caller-authored install authority is accepted and can advance the fresh incarnation. Pinning a trusted Ed25519 public key and verifying the exact canonical install content before the durable install write rejects both content tampering and a separately valid signature from an untrusted signer while preserving restart recovery and existing content-conflict semantics.

## Boundary

This is a deterministic single-process fixture with fixture-authored public-key trust. It does not establish key rotation/revocation, HSM/private-key custody, malicious trusted-signer resistance, distributed election, crash/power-loss fsync durability, simultaneous linearizability, external-effect safety, performance, or production exactly-once semantics.

## Next question

Keep authenticated install semantics fixed and vary only trusted-key rotation/revocation. Test whether an old-but-valid signer can continue minting new incarnation installs after key rotation versus a durable key-epoch/revocation boundary.
