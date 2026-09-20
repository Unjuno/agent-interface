# Issue #3660 independent raw-only audit

- Frozen PR head: `6c937af70f6861a7c83a3b17d5bb20588fb461e9`.
- Frozen preregistration SHA-256: `787f159f2c5ff7e2e017ef6e4d08ca1b843923d4e8c831b7659907a77ea18ffe`.
- Retained raw SHA-256 (reported by #3656): `f0df0248ff5e754a91e93271d9784f08d06ae1e8ff349b5f82f0fd015eb42883`.
- Local fixture is a verbatim JSON reserialization from the GitHub API payload; its whitespace may differ, so the reported byte SHA is not asserted against the fixture file. Event hashes are validated over the decoded event objects.
- Independent predicates: focus drift, modal transition/recovery, geometry/stale admission, Chromium replacement, and Calc return/stable control all recompute true from their retained event fields.
- Disposition: `HOLD_AUDIT_EVIDENCE_INCOMPLETE` due to absent `old_window_absent`, return `active_window`, and third event-level input-operation receipts. The top-level integer count is 3, but only two ledger events explicitly report `input_emitted: true`. No values were synthesized from `checks[]` or `fresh_validation`.
- The check vector agrees with the recomputed predicates, but is only a consistency comparison.
- Historical #3652 decision remains `HOLD_TASK_EFFECT_UNTESTED`; the predecessor PR and raw were not changed.
- Infrastructure: `STOP_CONTAINER_UNAVAILABLE` (Docker Desktop service stopped and daemon unavailable). No GUI, input, model, network, or formal allocation performed.
