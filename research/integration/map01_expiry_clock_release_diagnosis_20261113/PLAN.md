# MAP01 expiry clock and release diagnosis

Date: 2026-11-13  
Goal: identify whether the MAP01 20 ms expiry-boundary miss reflects a real
late release, a clock-domain/adjudication defect, or both, then run a fresh
integrated attempt without weakening any acceptance gate.

## What is wrong

The evidence does not say that every computer-control layer is broken. R142
produced the exact ammo effect (50→49), returned a W-up attempt, later observed
W and the mouse button neutral on the same target generation, completed a
two-second horizon, and passed its scoped demo check. It failed one hard gate:
the 41.941 ms interval between the last observed W-down sample and first
observed W-up sample exceeded the fixed 20 ms expiry bracket. The public graph
correctly remained `SAFE_YIELD / delivery_uncertain`.

R142 did not timestamp entry/return of the actual `SendInput` release calls, so
its 41.941 ms sample interval cannot be assigned to monitor wake, release
request, OS insertion, or readback latency. Its lease clock was Python 3.11
`GetTickCount64()` at 15.625 ms reported resolution, while the boundary sampler
also recorded `perf_counter_ns()` from QPC. The persisted samples show these
coordinates were not interchangeable: the last-down sample had a monotonic
midpoint of 244043515 ms and QPC midpoint 244043550.950 ms; the first-up sample
had monotonic midpoint 244043562 ms and QPC midpoint 244043593.0 ms. The audit
also treated a sample whose monotonic time equaled the serialized deadline as
fully after it. Thus the exact location of the deadline relative to QPC
observations is not established by R142, even though the QPC interval between
the two state reads is a real elapsed interval.

R157 supplies a useful contrast. Its deadline, sampler, and recovery-stage
trace used Python 3.14/QPC. It passed the unchanged 20 ms bracket (12.0785 ms),
observed the first fully post-expiry W-up at 10.7525 ms after expiry, and passed
the independent same-generation neutral horizon and exact-call ammo oracle.
The exact SendInput entries were +9.0401 ms and +9.7214 ms after expiry; their
returns were +9.6821 ms and +11.0081 ms. This localizes a substantial part of
that successful run to the recovery path, but is one attempt and does not
explain R142 or establish reliability. The 10 ms R142 versus 2 ms R139–R141
poll comparison remains chronological and confounded; it cannot establish
poll interval causality.

A new same-process probe corroborates the clock issue on this host. In 2,000
paired reads, Python 3.11.9 reported a median `perf_counter - monotonic`
difference of 21.75755 ms (range 21.5453–21.977 ms); Python 3.14.2, where
both clocks use QPC, reported median 0 ns (range −1,950 to 550 ns). The
persisted raw samples are in `clock-correlation-r01/`.

The shared adjudicator had a strictness defect: in
`research/integration/map01_numeric_ammo_oracle_20261111/input_boundary.py`,
it selects a fully post-deadline sample when
`monotonic_before_ns >= deadline_ns`. Equality only means the pre-read clock
value rounded to the deadline; it does not prove the read started after
expiry. R142's first down sample has both monotonic endpoints exactly equal to
the deadline, so it cannot be promoted as fully post-expiry. This does not
erase R142's conservative 41.941 ms last-down to first-up bracket or turn its
20 ms gate into a pass; the equality rows had inflated the intermediate
post-expiry-duration attribution. The helper now requires strict `>`, a
boundary-equality regression passes, and the corrected adjudicator was applied
read-only to retained R142. It excludes seven equality rows, changes the
post-expiry-down attribution from 39.9998 ms to 24 ms, and leaves the QPC gap
41.941 ms, outer bracket 42.1552 ms, and overall `not_verified` result
unchanged. The corrected output is retained separately; R142's original
result was not rewritten.

## Research plan

1. **Close the clock-domain ambiguity in the integrated path.** **Done for the
   QPC route:** retain the paired-clock probe and strict-equality fix. R158's
   public MCP preflight required same-host QPC and its deadline, sampler, and
   stage trace all used QPC. Python 3.11 `GetTickCount64` versus QPC remains an
   unqualified mixed-domain route. In any later runner, record
   `get_clock_info`, process/runtime identity, and paired `monotonic_ns` /
   `perf_counter_ns` readings in every process that contributes to a deadline
   or boundary decision. A sample is pre/post-deadline only when all timestamps
   used for the comparison are in one verified domain; do not infer an epoch
   conversion from nominal resolution. Equality with the deadline is not
   “fully after.”
2. **Keep latency stages distinct.** **Done for R158:** its QPC trace retained
   serialized expiry, recovery exchange, recovery send, both native
   `SendInput` entry/return spans, helper recovery entry and independent
   readback. The two native calls began +7.3236/+7.9675 ms after expiry; no
   span was dropped. Release request, API insertion, and neutral observation
   remain distinct evidence.
3. **Run one fresh native MAP01 attempt.** **Done as R158:** clean pinned
   source, unique process/window, passive CUA gate, one public dispatch, fixed
   10 s budget and 20 ms boundary, exact 50→49 task oracle, same-generation
   release, two-second neutral horizon and same-run demo analysis. All 19
   runtime gates passed; no retry or replay. Preserve the clerical prereg
   attempt-label mismatch as an explicit deviation; do not edit frozen files.
4. **Decide from the evidence.** R158 shows the QPC-native integrated route
   can meet the 20 ms gate in one attempt, while R142 remains a real
   conservative 41.941 ms bracket miss and its release-call latency is unknown.
   The clock mismatch and equality bug explain why R142's intermediate timing
   attribution was unreliable; they do not erase its gate failure or prove the
   sole physical cause. Any missing identity, clock metadata, recovery receipt,
   task effect, or horizon remains FAIL/UNKNOWN.

## Next unresolved boundary

The present diagnosis step is complete. The full computer-control goal is
still open. R158 exercised automatic public lease-expiry recovery, but it did
not force the exception-only native continuation path or prove absence of all
queued OS/application effects. The next discriminating live step is one fresh,
isolated native exception-path attempt using the same QPC stage tracing, exact
call/task oracle, same-generation release and two-second neutral horizon. Keep
the original terminal UNKNOWN and replay denial semantics. Follow with
delayed-effect observation beyond the horizon before broadening reliability
or #57 economics claims.

## Completion criteria for this diagnosis step

- The R142 failure is described without conflating the exact task effect,
  eventual neutral state, and strict timing gate. **Done.**
- The clock-coordinate mismatch and missing SendInput-stage timestamps are
  directly evidenced and the uncertainty is explicit. **Done.**
- The shared boundary adjudicator rejects deadline equality, its regression
  passes, and the corrected R142 derivation is retained separately from the
  original result. **Done:** 59 tests pass normally and under `-O`.
- A fresh attempt uses a single verified time domain for all deadline
  adjudication and retains raw conditions/results with no weakened gates.
  **Done for one scoped sample:** R158, all 19 gates passed; raw and final
  packet manifests verified.

The clock/adjudication diagnosis and one QPC-native integrated attempt are now
recorded. They do not prove a cause for R142, establish reliability, clear
MAP01, exclude every queued effect, or provide an efficiency comparison for
Issue #57.
