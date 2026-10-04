# T5 result — offline timestamp-order construction

The current-main analyzer at `e561b25b700680df4e6ffd2b92faf1dde1682ef7` accepted both invalid event sequences in the frozen corpus while accepting the two positive controls. The independent audit reported `FAIL_TIMESTAMP_ORDER_NEGATIVE_ACCEPTED` for `ack_before_admission` and `release_return_before_start`, with zero raw-integrity errors.

The source now checks that admission, input acknowledgement, release-call start, and release-call return timestamps are nondecreasing before it emits a retained interval. Equality remains accepted. On the same four cases, the repaired analyzer passed all four classifications and the independent audit reported `PASS_ORDER_GATE_CONSTRUCTION_SCOPED`, with no false accepts or integrity errors.

The source unit suite passed 5/5. The independent auditor tests passed 4/4, including mutations to a repaired classification and frozen case bytes. Python compilation and `git diff --check` passed. Exact invocations and scope are recorded in `RUN.json`; the baseline, repaired source, raw candidate JSON, audited JSON, and case corpus are retained beside this report.

This repairs the offline readiness classifier only. It does not demonstrate malformed live timestamps, X11 behavior, physical release, exact key-up time, occupancy, useful feedback, recovery benefit, task effect, or MAP01 success. The explicit X11 fixture allocation in #5156 remains unassigned and untouched. The broader #59 matched threat-control gate also remains open.
