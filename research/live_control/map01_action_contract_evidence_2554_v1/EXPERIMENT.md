# Action-contract evidence retention scaffold

Successor #2631. This path does not reconstruct missing #2585 rows and does not claim a new experiment. It provides a fail-closed offline auditor for a future ten-row construction record.

Required row fields: case_id, arm, dwell_tics, emitted_vector, declared_button, ready, pre, post, screen_hash_before, screen_hash_after, process_identity, cleanup_ok. The accepted case set is the Cartesian product of arms forward/use/left/right/noop and dwells 4/16, exactly once.

H/T/D/C/U:

- H: a dwell-boundary result is auditable only when raw rows and identity/cleanup receipts are retained.
- T: validate ten supplied first-result rows and independently recompute mapping, uniqueness, readiness, identity, and cleanup.
- D: raw JSONL, manifest, source/container/package/fixture identities, auditor hash, and authoritative workflow status.
- C: PASS_CONSTRUCTION_EVIDENCE_RETAINED only for an exact ten-row audit; missing original rows are not reconstructed.
- U: original #2585 raw rows are not currently recoverable from that PR.

No model, GUI transport, X11 input, formal gameplay, or production claim.
