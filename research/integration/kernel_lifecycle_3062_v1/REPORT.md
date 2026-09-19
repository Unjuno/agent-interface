# Kernel lifecycle adapter matrix

Issue: #3062

## H/T/D/C/U

- H: the existing lifecycle/result adapter preserves positive, refusal, stale, ambiguity, partial, cleanup-failure, and release distinctions across native Python and Docker.
- T: execute the existing frozen eight-case GTK matrix in native Python and in a network-disabled Docker container; compare dispositions, receipt order, independent gate, release/cleanup fields, and retained raw rows.
- D: Docker image agent-interface-2994:20260920, digest sha256:167fd6184cac8729ccfea407938943384d64fe2999e7319bed3587638fa94b7c. Docker matrix completed with actual=expected dispositions, formal receipt order true, independent gate classified all cases, scorer match true. Native command used the same runner and current source.
- C: HOLD_KERNEL_LIFECYCLE_EVIDENCE_INCOMPLETE. Native execution stopped before matrix start because Xvfb is unavailable on the macOS host. This is an infrastructure stop, not a lifecycle pass/fail. Docker evidence alone cannot satisfy the required native/container agreement.
- U: all Docker raw rows and stdout are retained in the external allocation used for this run; this compact result does not claim full acceptance. A future rerun needs a native Xvfb-capable environment or a native headless backend that preserves the same matrix semantics.

Cases: useful, unavailable, guarded, no_effect, partial, stale_repair, ambiguous, cleanup_failure. Model and network calls were zero.
