# W2 lease-close candidate/raw-oracle matrix — host construction

Additive candidate extension to [Issue #5127](https://github.com/Unjuno/agent-interface/issues/5127). The preceding frozen-checker counterexample remains unchanged in the parent package.

## H/T/D/C/U

**H.** A conservative candidate plus a separately launched raw-only oracle can retain pre-close authorization while rejecting post-close edges, holding uncertain interval overlap, and refusing to infer the meaning of missing/foreign close-actuation lineage.

**T.** With the exact eight-case frozen W2 fixture, version only `release-before-terminal`'s `LEASE_OPEN.actuation_id` to A4, then run six fresh candidate/auditor CLI pairs: no close, a close after both edges (450 ns), a close before both edges (50 ns), an edge bracket overlapping the 50 ns close, a foreign close actuation, and a missing close actuation. Each raw auditor receives the complete versioned eight-case trace and independently reconstructs every case. A separate tamper run changes one candidate row and requires nonzero audit exit.

**D.** All six raw audits must return `PASS_CLOSE_ORDER_RAW_AUDIT_SCOPED`, errors=[], 8/8 case identity agreement, and 14 reconstructed decision rows. Target rows: no-close and pre-close `AUTHORIZED_MATCH` 2/2; post-close `REJECT_EDGE_AFTER_LEASE_CLOSE` 2/2; overlap `HOLD_EDGE_CLOSE_ORDER_UNCERTAIN` for the overlapping down edge and reject the later up edge; foreign/missing close lineage `HOLD_CLOSE_LINEAGE_UNRESOLVED` 2/2. The tamper auditor must exit 1 on `candidate_raw_disagreement`.

**C.** Original fixture bytes remain unchanged; each variant starts from an in-memory copy with the same A4 open binding. The only variant difference is close presence/time/lineage, except the explicit overlap case which widens the down-edge transition interval to straddle the close. Same synthetic monotonic clock, lease, and actuation. Candidate and raw oracle are separate modules and separate CLI processes.

**U.** Python 3.12.10 Windows host CPU only. No Docker/formal execution, live authority, GUI/model/task effect, or runtime integration. Foreign/missing close lineage is held conservatively pending a contract decision; this does not establish whether a close is lease-wide or actuation-scoped.

## Result

`PASS_HOST_CLOSE_ORDER_CANDIDATE_MATRIX_ONLY`: the combined v1/v2/v3 plus close-order candidate host unit suite passes 21/21, all six retained raw CLI audits pass, each reconstructs 14 decisions over eight cases, and the independent tamper run exits 1. Raw traces and candidate/audit reports plus SHA-256s are retained under `matrix/` and in `RESULT.json`.

This does **not** erase or supersede `FAIL_W2_CLOSE_ORDER_CHECKER_DISAGREEMENT`: the frozen verifier still accepts the post-close treatment, while the frozen raw auditor rejects it. This candidate only demonstrates an additive proposed boundary policy and its scoped controls. It is not a merged fix or formal acceptance.

## Next gate

Review the conservative edge/close interval policy, then refreeze all current-main source identities and run the candidate plus independent audit in a pinned Docker Desktop CPU container only after explicit owner transfer. Foreign/missing close semantics remain a separate contract decision. Keep PR #5129 open and draft until a reviewed repair path and gated container record exist.
