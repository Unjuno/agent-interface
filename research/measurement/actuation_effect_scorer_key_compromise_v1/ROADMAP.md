# ROADMAP — ACTUATION-EFFECT-SCORER-KEY-COMPROMISE-20260918-001

H: Conditional on compromise of the current scorer HMAC key, a single-root receipt verifier cannot distinguish trusted scorer provenance from compromised producer provenance when verifier-visible receipt bytes are identical, while wrong-key or post-signature mutation remain rejectable.
T: Freeze one receipt schema/verifier, paired TRUSTED/COMPROMISED hidden provenance over identical bytes, wrong-key and altered controls, source-first publication, then 4 immutable batches x 50,000 pairs.
D: PASS iff legitimate accept=100%, compromised accept=100%, visible-byte identity=100%, wrong-key reject=100%, altered reject=100%, authority promotions=0, integrity passes.
C: This is conditional on key compromise; it does not imply compromise likelihood and does not test multi-root repairs.
U: Standard-library synthetic cryptographic boundary only; no GUI/X11/model/network/task input.
STOP: No repair mechanism, rerun, or tuning.
