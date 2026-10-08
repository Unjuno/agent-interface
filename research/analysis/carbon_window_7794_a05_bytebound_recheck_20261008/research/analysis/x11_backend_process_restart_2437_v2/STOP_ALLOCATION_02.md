# Allocation 02 — formal evidence STOP

- Allocation: `X11-BACKEND-PROCESS-RESTART-2437-20261001-02`
- Frozen main: `d077494b50341f638e6d66f63e817ec48923768d`
- Freeze/formal candidate source: branch `research/2437-backend-process-restart-xvfb-v2-20261001`, commit `de3c8d96885b912b22ae0e5fd6252c76db223d6c`.
- Candidate invocation count: **1**, process exit 0.
- Raw-only auditor invocation count: **1**.
- Disposition: **STOP_AUDIT_ERRORS**. Auditor receipt reports missing `key_down_after_explicit_cleanup`, `cleanup_owner`, and parent-level `dispatch_now_ns`.
- Raw length: 1,990 bytes. SHA-256 recorded by the one auditor read: `45d698cf47954d78572e39f602bf14064504595cc4233c17b66a19e61e9e2b65`.
- No scientific PASS/FAIL is assigned. Do not rerun candidate/auditor and do not inspect/parse the raw. Preserve it byte-for-byte for publication.
- Read-only source diagnosis (not raw reinspection): the parent runner referenced `session.recovery_required` even though `session` exists only in the dispatch child, before writing explicit-cleanup fields; it also failed to copy the child dispatch timestamp into the parent raw. The one-audit raw schema gate correctly refused to infer missing observations. This source-level defect motivates Allocation 03's tested record-assembly helper; the scientific hypothesis/environment remain unchanged.
- No retry or pooling. Allocation 03 is prospectively versioned with a changed, separately tested recording boundary.
