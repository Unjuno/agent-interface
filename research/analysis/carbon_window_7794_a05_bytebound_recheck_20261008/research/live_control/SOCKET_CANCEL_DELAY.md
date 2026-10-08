# Observation waits must not serialize cancellation

Frozen event_socket_v2 serves requests serially. A live private-X11 xterm probe
starts a four-second Right-key hold, then a two-second read for an event that will
not occur. A clock command forwarded with that read proves its handler is active
before the probe sends cancel. Cancellation waits behind the observation request.

Candidate event_socket_v3 uses ThreadingMixIn with eight nonblocking admission
slots. Excess connections receive busy/command_forwarded=false; command writes
still pass through the same CommandOnce serialization and runtime admission.
The same workload lets cancel proceed while the observation read waits.

| Metric | Serial v2 | Bounded concurrent v3 |
|---|---:|---:|
| Cancel request to response containing cancel_requested | 1987.804 ms | 48.619 ms |
| Cancel request to verified input release | 1975.731 ms | 93.275 ms |
| Verified release before long read returns | No | Yes |

Cancellation acknowledgement is not release. These timestamps come from the
same Linux monotonic clock. Actual input-admission records precede verified
release; both programs terminate cancelled. The audit checks listed source hashes
and 22 exact public AIT/PNG frames across successful cohorts (20 serial, 2 concurrent).
These are one scripted run per implementation, not assistant reaction performance.

Both runs also send a clock request and disconnect before reading its reply,
then repeat its request ID and payload. The reply is marked replayed and runtime
clock count is three total (initial, blocker, dropped/retried), proving no second
clock command in these live cases. This is a benign command retry test, not a
server-crash or ambiguous side-effect recovery guarantee.

The first concurrent attempt returned an empty five-second startup timeout; the
probe incorrectly indexed its empty records and finished cleanup. Cohort 02 is
retained. Probe v3 waits again on the same live process/cursor on startup timeout,
and cohort 03 completes. This corrects the experiment driver, not application
readiness semantics. No failed cohort is overwritten.

Limits: all eight occupied slots can still reject a cancellation connection;
there is no reserved control capacity or priority queue. Synchronous blocked stdin
writes still hold the write registry lock. Slow clients consume one slot each;
busy-path saturation, interrupted-parent cleanup and restart behavior remain to
be tested. Daemon handlers are not durable pending work. No input lease is extended,
and timeout is not application termination. This is a private transport candidate,
not a general cancellation-latency guarantee or default promotion.

Evidence: `results/socket-cancel-delay-01`, `-02`, `-03`, plus
`results/socket-cancel-delay-audit.json`. Next test saturation and distinguish
control admission from observational capacity before relying on this bridge for
continuous control. Keep the serial failure as the regression baseline.
