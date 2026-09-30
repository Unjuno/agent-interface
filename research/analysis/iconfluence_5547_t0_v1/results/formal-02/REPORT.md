# Issue #5547 T0 formal-02 result

## Result

`PASS_ICONFLUENCE_FINITE_MODEL_SCOPED` under the frozen 2-replica finite model. The candidate emitted 100 operation/value pairs. A separate raw-only auditor independently reconstructed every joined state, checked the invariant, operation classification, reverse-order equality and 10 same-delta idempotence cases. It found zero unsafe pairs among the 36 pairs classified `monotone_safe`. Each `REFRESH_EPOCH`, `RESERVE_QUOTA`, and `COMMIT_EFFECT` operation had at least one joined invariant-violating witness (2, 8, and 20 witness rows respectively). Five corruptions—wrong safe label, wrong operation classification, flipped verdict, dropped pair, and forged joined state—were all detected.

Formal candidate container exited 0 in 1,054 ms. The candidate JSON SHA-256 is `f73b40f167fa06752039bb64dc3a7aaa1d9bf5df33924194646ea30e2d47ab38`. Independent audit and controls also exited 0. Exact runtime/image/configuration and raw digests are in `RUN.json`, `audit.json`, `controls.json`, and `SOURCE_SHA256.json`.

## Interpretation

The result supports only this declared finite example: set-union evidence/revocation/receipt deltas preserve the encoded invariant for the enumerated pairs, while the three selected coordination-required operations have finite counterexamples. The formal-01 FAIL remains part of the evidence: integer quota deltas lost operation identity, and addition violated same-delta idempotence. The explicit reservation-ID set in formal-02 resolves that representation defect while retaining the independent-reservation conflict witness.

## Limits

This is a hand-specified model, not a discovery algorithm for arbitrary operations. “Coordination required” means only that this finite model contains an invariant-breaking merge involving that operation; no particular lock, quorum, or distributed protocol was tested. The boolean effect and two replica identities are deliberately narrow. External effects, real authority/freshness semantics, scheduler behavior, transport, latency, availability, production schemas, empirical coordination cost, and cross-domain transfer are untested. A green checker does not prove the model complete or the real system safe.

## Reproduction

Use the digest-pinned Python image and network-disabled/read-only Docker configuration in `FREEZE-02.json`. The exact executed artifacts and source hashes are retained beside this report. Do not rerun either consumed allocation identity; a changed model requires a new successor identity and output path.
