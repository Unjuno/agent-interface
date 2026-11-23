# R40 result — public oracle rejected event time semantics

Disposition: STOP_ORACLE_TIME_OUTSIDE_REQUEST_WINDOW_AFTER_B_RELEASE. The single allocation is consumed; no retry was made.

The source A action remained UNKNOWN with release unconfirmed, task success null, and replay denied. Public orphan recovery confirmed release, neutral readback, and the 2 s horizon. The newly-created target generation then accepted B; public action status was completed and release confirmed. The independent fixture event log contains exactly one B WM_CHAR in the dispatch interval and fresh state b.

Public task verification returned UNKNOWN with task_success null. The oracle returned the original WM_CHAR event timestamp as observed_monotonic_ns, but runtime requires this timestamp within the oracle request/receipt window; the event necessarily preceded the later verification request. The durable custody fence is clear. Fixtures remain open because public verification did not pass.

The next allocation should preserve the event-time interval check inside the oracle, but stamp the verification receipt with a monotonic observation time at or after the oracle request. This is a receipt protocol correction, not a change to the task criterion.
