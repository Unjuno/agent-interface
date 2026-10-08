# Issue #6710: independent controller-law replay

Audit-only successor to #6650 / PR #6670. It preserves the predecessor's adverse `FAIL_HYPOTHESIS` result and raw bytes. No controller candidate is rerun; one independently authored raw-only auditor reconstructs all four policies from the exact frozen fixture and compares every recorded field.

The replayer does not import the predecessor candidate or accounting auditor. It separately builds per-tick arrivals, pending work, source generations, per-session queue signals, controller dwell/recovery state, producer suppression, service starts, and terminal outcomes. The focused unit suite is construction evidence; the formal auditor is run exactly once in a digest-pinned network-disabled OrbStack container after the freeze.

Scope is finite synthetic audit-conformance only. Even an exact replay does not validate the original hypothesis, prove that persistence throttling is useful, or support production, GUI, user, task-correctness or safety claims.
