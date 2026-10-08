# MAP01 terminal-sync diagnostic successor #3211

This is an additive diagnostic copy of the frozen #3202 runner. It changes only JsonSession event retention: every JSON event read from the child stdout is appended immediately to the arm runtime as session-events.jsonl.

It does not change allocation IDs, fixture, arms, thresholds, timeout values, authority, or formal decision logic. It must not rerun the consumed allocation map01-recovery-cover-matched-live-v2-02.

H/T/D/C/U:
- H: retaining the reader-side event stream on exception will distinguish missing emission, ID mismatch, delayed delivery, and cleanup loss at the fallback terminal boundary.
- T: run syntax/unit checks and one bounded diagnostic invocation under a fresh non-formal diagnostic allocation; preserve the first trace and traceback.
- D: PASS_MAP01_TERMINAL_TRACE_DIAGNOSTIC only if the timeout boundary and terminal/release event cardinality are independently classified from the retained trace. HOLD if the child or runner cannot produce a trace. This is not a formal recovery result.
- C: the timeout may be caused by child lifecycle, queue ordering, mismatched ID, or hosted-runner timing; trace retention does not prove which explanation until executed.
- U: no live recovery efficacy, model benefit, task effect, or production claim.

Historical #3202 remains unchanged.