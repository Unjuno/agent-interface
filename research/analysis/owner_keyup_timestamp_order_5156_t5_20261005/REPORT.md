# T5 result — offline timestamp-order construction

The analyzer at frozen main `e561b25b700680df4e6ffd2b92faf1dde1682ef7` accepted both invalid event sequences in the frozen corpus while accepting the two positive controls. Main later advanced through `ec71c53411055b1d3960ca7c947b52a70c5dca2f`; the analyzer blob remained `f3d5fe315df8f4296351f1a5fc666d50ecaa6745`. The independent audit reported `FAIL_TIMESTAMP_ORDER_NEGATIVE_ACCEPTED` for `ack_before_admission` and `release_return_before_start`, with zero raw-integrity errors.

The source now checks that admission, input acknowledgement, release-call start, and release-call return timestamps are nondecreasing before it emits a retained interval. Equality remains accepted. On the same four cases, the repaired analyzer passed all four classifications and the independent audit reported `PASS_ORDER_GATE_CONSTRUCTION_SCOPED`, with no false accepts or integrity errors.

The source unit suite passed 5/5. The independent auditor tests passed 4/4, including mutations to a repaired classification and frozen case bytes. Python compilation and `git diff --check` passed. Exact invocations and scope are recorded in `RUN.json`; the baseline, repaired source, raw candidate JSON, audited JSON, and case corpus are retained beside this report.

After rebasing, one verification replay stopped with `STOP_AUDIT_INTEGRITY` because the Windows worktree still held CRLF copies while the committed package and raw hashes were LF. That first stop is retained in `output/post_rebase_checkout_stop.json`. No candidate was rerun; restoring all tracked package bytes from the exact Git blobs returned the checkout to LF and the same stored outputs passed all four auditor tests.

This repairs the offline readiness classifier only. It does not demonstrate malformed live timestamps, X11 behavior, physical release, exact key-up time, occupancy, useful feedback, recovery benefit, task effect, or MAP01 success. The explicit X11 fixture allocation in #5156 remains unassigned and untouched. The broader #59 matched threat-control gate also remains open.
