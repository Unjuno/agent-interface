# #6501 actual waiter-deadline construction A01

Worker 01a0ff2d-be6f-78d3-ad7c-497514c9079f, FINAL-v5. New native Windows
construction, not replay of T0/T0b/6890 or the active blocking-thread exit study.
No runtime, actuation, model, container, socket, GPU or shared resource is used.

H: successful await does not prove a waiter's deadline still holds. Shield
preserves a companion while a separate delivery-time check refuses late results.
T: 3 fixed policies × 5 authored schedules × 2 producer cancellation behaviors:
30 rows / 60 waiter outcomes. All calls share one same-scope producer per row.
Policies: direct wait_for; shielded wait_for; shielded wait_for plus strict
per-waiter perf-counter deadline check. Schedules: fresh, already expired,
deadline signal while producer pending, admission delay after result, UNKNOWN.
No dynamic joining or generation change is modeled; those have other owners.

Producer cancellation either propagates or is suppressed with an authored
100ms asynchronous cleanup before returning READY. This is a planted bounded
noncooperative coroutine, not measured backend I/O. Pending producers are released
and every task is joined before the next row; no task/process escapes the study.

Expired/future timeout intervals use 50ms; fresh/UNKNOWN use 1s. The admission-
delay fixture sleeps past its 50ms deadline plus 40ms. Construction first tried
5ms: Windows asyncio timed out before the high-resolution deadline while data
was already produced. That failed attempt/source/log is retained. Windows loop
monotonic resolution is 15.625ms here. This pre-freeze repair uses a timer above
two clock resolutions. The raw includes actual perf-counter timestamps; a
TimeoutError is never itself treated as proof of expired physical time. No
clock-domain equality or precise timer enforcement is assumed.

D: all fresh positives, UNKNOWN refusals, cancelled companion states and cleanup
must match the frozen table and exact event sequence. Returned values in authored
late schedules must actually be late by the same perf-counter clock or the audit
FAILS. Deliberate late admissions in unguarded policies are retained negative
controls. Guarded policy must have no late admission and preserve fresh positives.
Eight copied-output controls must all reject. No host timing speedup is tested.

C: wrapping shared work in wait_for is not a physical deadline guarantee;
cooperative cancellation, application delivery checks and lifetime ownership are
different responsibilities. Shield alone does not validate result freshness.
U: descriptive read-only evidence, authored barriers/delays and this exact
interpreter/host. No GUI T1, native currentness/release, thread exit, throughput,
useful task effect or production adoption follows from this construction.

One actual comparative matrix and one independent raw-only auditor invocation,
zero retries; fresh exclusive output paths; one tiny native process at a time,
outer matrix timeout 10s and <=1MiB raw. Earlier construction tests are repairable
engineering checks with all first failures retained. The matrix cannot be rerun
to obtain PASS; FAIL/STOP remains its first outcome. Freeze source/runtime/input
hashes before collection. Deadline origin/effective N are unconfirmed and unchanged.
