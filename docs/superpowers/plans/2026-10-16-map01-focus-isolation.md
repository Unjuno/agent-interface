# MAP01 selected focus-query isolation

Base `41946fdf1c661d5209aa834494e1137179e33ad3`. Continue the authorized
Fake X-only integration with no live allocation or new approval/quorum rule.

Root cause: V12's selected process reader was separate, but `invalid_focus`
still synchronously queried the input connection before held cancellation and
expiry cleanup. First Fake X RED confirms no interruption while focus is stalled.

Use the same independently owned read-only target worker for exact numeric focus
queries in the explicit process-identity selection. Preserve exact-focus equality
and pointer's existing additional validation; do not substitute subtree focus.
Preserve original perf-counter deadline/cancel/stop checks and sticky retirement.
Release never needs the focus reader. Keep default owner behavior and telemetry.
Distinguish unavailable target query from an actually observed focus change.

- [x] Reproduce selected-owner blocked-focus cancellation failure before repair.
- [x] Route selected lease-bound focus reads through the read-only worker.
- [x] Check owner cancellation/expiry, malformed/failed focus and observed change.
- [x] Check actual composed Executor/V4/V12 cancel and verified fake release before
  the focus read resumes. Keep final-focus source/cancel/deadline mutation cases.
- [ ] Run affected normal/-O regressions, retain exact source/first outcomes,
  obtain bounded read-only review and integrate verified source.

No physical I/O bound follows. Native input send/sync/readback, pointer geometry,
hit testing, idle observation and close remain separate blocking boundaries.
Read-only transport cancellation retires rather than forcibly closing a blocked
X client; a daemon can remain pending until that native read returns.
