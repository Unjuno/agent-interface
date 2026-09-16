# Rooted signer recovery v1

Task: `COORD-ROOTED-SIGNER-RECOVERY-20260917-029`

Decision: **`PASS_ROOTED_SIGNER_RECOVERY_SCOPED`**

## Method

Container-first deterministic state machine. Related Issues were reviewed before claim: #104/#105 support the one-variable discovery loop; #59 keeps real-time control as primary; active #626 already owns the real MAP01 handoff transfer, so this rung uses no scarce live/model allocation.

Ed25519 operational/recovery keys were generated only in-memory to construct fixed fixtures. No private-key file is retained. Exact `model.py`, `test_model.py`, `run_experiment.py`, `verify.py`, and `fixtures.json` bytes were SHA-256 frozen before formal execution.

Checks: `py_compile` PASS; 9/9 deterministic unit tests PASS; formal runner invoked once; `verify.py` PASS; formal reruns 0; post-result SHA recheck 5/5 PASS.

## First outcome

- compromised-current-signer baseline: K2/e2 signs a normal rotation to attacker/e3; rotation is accepted, attacker signs I3 install, and fresh work advances generation 5→6;
- rooted recovery: independently pinned recovery root signs K2/e2→K3/e3; recovery succeeds without a K2 signature, old K2/e2 install becomes `STALE_INSTALL_KEY_EPOCH`, K3/e3 install succeeds, fresh work advances exactly once;
- forged recovery signed by K2 rather than recovery root returns `RECOVERY_SIGNATURE_INVALID`, recovery writes 0;
- restart reconstructed from the durable recovery receipt restores K3/e3, keeps K2 stale, and accepts K3 work;
- exact recovery replay is `ALREADY_RECOVERED_SELF`; same recovery ID with changed root-signed content is `RECOVERY_RECEIPT_CONFLICT`; recovery epoch gap fails closed.

## Interpretation

A current-signer-only rotation chain cannot recover from compromise of the current signer because the compromised signer can validly authorize its own successor. A separately pinned recovery authority provides an independent escape hatch in this scoped fixture: it can replace K2 without K2 cooperation and preserve stale-epoch rejection afterwards.

This is additive coordination evidence, not a reason to displace the active real-time-control lane. It consumes no GUI/model/game allocation.

## Boundary

The recovery root is fixture-authored and assumed uncompromised. No threshold recovery, root compromise, HSM custody, distributed election, power-loss durability, external effects, or production exactly-once claim. A next coordination question should be threshold/root-compromise recovery only if integration needs justify it; Issue #57/#59 sequencing should otherwise take precedence.
