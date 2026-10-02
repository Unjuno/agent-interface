# Issue #5970 retained-trace applicability T1

This read-only successor inspects a frozen retained X11 reconnect archive to answer whether the cross-source causal-cut question from #5970/#5348 can be evaluated on existing records. It scans the four `REBOOTSTRAP_ON_RECONNECT` disconnect-press/release cases across two repetitions; no consumed allocation is rerun or regraded.

The archive is verified from frozen Git blobs and parsed in memory. The candidate checks raw/aggregate event agreement, reconnect-epoch binding, and explicit cross-source causal-parent/message fields. The independent auditor reconstructs those facts separately. See `PLAN.md` for H/T/D/C/U and `REPORT.md` for the adjudicated result.

This is posthoc trace applicability only. It does not infer causality from shared monotonic timestamps and does not add authority to the historical X11 bootstrap result.
