# Durable authenticated key-rotation receipt v1

Task: `COORD-DURABLE-AUTH-KEY-ROTATION-20260917-028`

Decision: **`PASS_DURABLE_AUTH_KEY_ROTATION_RECEIPT_SCOPED`**

## Method

Container-first deterministic state-machine experiment. GitHub is allocation/publication only. K1/K2/attacker Ed25519 private keys were used only to create fixed fixtures and were deleted before the formal SHA-256 freeze. Formal runner invocation count: one; reruns: zero.

## First outcome

| Case | Outcome |
|---|---|
| mutable K1→K2 rotation, then rotation state rollback to K1 | old K1/epoch1 I2→I3 install `INSTALLED`; fresh I3 work `APPLIED`, generation 6 |
| durable K1-signed rotation receipt survives mutable rollback | `KEY_ROTATION_STATE_ROLLBACK`; stale K1 install write 0 |
| restart from durable authenticated rotation receipt | reconstruct K2/epoch2; old K1 `STALE_INSTALL_KEY_EPOCH`; K2 install accepted; fresh I3 `APPLIED` once |
| attacker-signed forged rotation | `ROTATION_SIGNATURE_INVALID`; rotation write 0 |
| exact rotation replay | `ALREADY_ROTATED_SELF` |
| same rotation ID / changed valid K1-signed content | `ROTATION_RECEIPT_CONFLICT` |
| skipped epoch | `ROTATION_EPOCH_GAP` |
| predecessor signer mismatch | `ROTATION_PREVIOUS_SIGNER_MISMATCH` |

## Container checks

- `py_compile`: PASS
- deterministic unit tests: 9/9 PASS
- formal runner: 1 invocation
- `verify.py`: `PASS_VERIFY`
- post-result source/fixture SHA recheck: 5/5 PASS
- formal reruns: 0
- retained private-key files: 0

## Interpretation

Current-key-epoch revocation is insufficient if the rotation state itself can regress independently. Mutable-only rollback revives old K1 signing authority. A content-bound K1-authenticated durable K1/e1→K2/e2 rotation receipt detects that regression before install admission and reconstructs K2/e2 after restart. A caller-forged rotation fails signature verification before any durable rotation write.

## Boundary

K1 is trusted to authorize K2 rotation by construction. One rotation only; restart verification uses the pinned genesis K1 public key. This is not a multi-hop rotation-chain/compaction proof, malicious-current-signer solution, HSM custody proof, fsync/power-loss proof, distributed consensus, simultaneous linearizability, external-effect, performance, or production exactly-once result.

## Next question

Keep rotation receipt semantics fixed and vary only compromise/recovery of the currently authorized rotation signer. Test whether a separately rooted recovery authority can replace a compromised current signer without reactivating older install authority.
