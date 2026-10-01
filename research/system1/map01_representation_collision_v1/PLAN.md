# MAP01 typed representation collision v1

Task: `LOCAL-SYSTEM1-MAP01-TYPED-REPRESENTATION-COLLISION-20260917-001`

Base: `048b76c917a2013b0bc3f3264466562d87860f0f`
Issue: #937
Held-out source allocation: `map01-soft-context-v31-live-01`
Held-out report Git blob: `2aed2e7e3f58b4f8b013fc98c79482a4036225ae`
Decision directories: `decision-0` through `decision-7` only.

Formal representation and inclusion rule are exactly those in Issue #937. Input signature is the exact `prompt.txt` bytes. The formal materialization file stores those bytes as base64 plus source Git blob identities. Teacher label is canonical JSON of the retained action after removing only `assessment`. Image hashes are diagnostic only and are prohibited from the signature.

Formal invocation count: 1. Reruns/replacements: 0. No training, model call, GUI/game input, authority action, threshold tuning or source mutation.

Decision:
- PASS_TYPED_REPRESENTATION_COLLISION_REPLICATED_SCOPED: integrity passes and at least one eligible exact-prompt group contains >=2 distinct canonical structured labels.
- HOLD_NO_HELDOUT_COLLISION: integrity passes, >=2 eligible rows, no collision.
- HOLD_INSUFFICIENT_ELIGIBLE_ROWS: <2 eligible exact-source rows.
- FAIL_INTEGRITY: source/canonicalization/signature contamination or formal replay violation.
