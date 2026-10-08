# Current-key compromise boundary result

Decision: **PASS_SINGLE_ROOT_COMPROMISE_INSUFFICIENT_SCOPED**.

Exact #1272 single-root verifier semantics were preserved from authoritative predecessor SHA-256 `7d264de601f475d0face9b4b4860cd58a4389133407f9fcb3fcde013ade94cdd`. The sole changed factor was adversary knowledge of the current active HMAC key; hidden producer provenance was visible only to the independent oracle.

- formal: 4 immutable batches × 50,000 pairs = 200,000 legitimate/compromised pairs; batch reruns0.
- legitimate current receipts accepted: 200000/200000.
- compromised-current-key forged receipts accepted: 200000/200000.
- verifier-visible receipt equality: 200000/200000.
- candidate decision equality within each pair: 200000/200000.
- independent MAC-validity oracle accepted both members: 200000/200000 legit and 200000/200000 forge.
- hidden oracle classified compromised accepted receipts as compromised: 200000/200000.
- authority/task-success promotions: 0/0.
- frozen audit PASS; copied-summary corruption controls 5/5 rejected; postformal source rehash all exact.

Scoped interpretation: **a verifier whose only trust root is the currently active shared HMAC key cannot distinguish a trusted runtime receipt from a forge authored by an actor that possesses that same key while continuing to accept legitimate current receipts.** Epoch binding remains useful against retired-key receipts, but it does not solve current-key compromise. This is an impossibility/boundary result, not evidence that compromise is likely and not a repair recommendation by itself.
