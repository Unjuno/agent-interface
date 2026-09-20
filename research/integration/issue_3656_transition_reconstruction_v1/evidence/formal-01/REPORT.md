# Issue #3660 independent raw-only audit

- Frozen PR head: `6c937af70f6861a7c83a3b17d5bb20588fb461e9`.
- Frozen preregistration SHA-256: `787f159f2c5ff7e2e017ef6e4d08ca1b843923d4e8c831b7659907a77ea18ffe`.
- Retained raw SHA-256 (reported by #3656 and independently rechecked over the exact GitHub Contents API bytes): `f0df0248ff5e754a91e93271d9784f08d06ae1e8ff349b5f82f0fd015eb42883` (7644 bytes).
- The committed local fixture is a JSON-semantic reserialization from the GitHub API payload, SHA-256 `ef4b66777da5acaf70588120b4bcc5ca5dc9efc9716c8486dc63a2e382ddc281`; it is not byte-identical raw and cannot pass the CLI's frozen digest gate. The exact upstream Git object is the authoritative CLI input (`git show FETCH_HEAD:<frozen-path> | python audit_transition.py -`).
- Independent predicates: focus drift, modal transition/recovery, geometry/stale admission, Chromium replacement, and Calc return/stable control all recompute true from their retained event fields.
- Disposition: `HOLD_AUDIT_EVIDENCE_INCOMPLETE` due to absent `old_window_absent`, return `active_window`, and third event-level input-operation receipts. The top-level integer count is 3, but only two ledger events explicitly report `input_emitted: true`. No values were synthesized from `checks[]` or `fresh_validation`.
- Exact frozen Git object was streamed into the CLI from WSL; the CLI independently calculated the expected 7644-byte SHA-256 and returned the same typed HOLD, with all five transition predicates true and zero structural/hash errors.
- The check vector agrees with the recomputed predicates, but is only a consistency comparison.
- Historical #3652 decision remains `HOLD_TASK_EFFECT_UNTESTED`; the predecessor PR and raw were not changed.
- Infrastructure: `STOP_CONTAINER_UNAVAILABLE` (Docker Desktop service stopped; daemon unavailable; service start denied). Audit was executed in Windows Python and independently in WSL Ubuntu, not in a container. Both yielded 13/13 mutation tests. The byte-bound Git-object CLI audit in WSL returned the same three-item HOLD. No GUI, input, model, network, or formal allocation performed.
