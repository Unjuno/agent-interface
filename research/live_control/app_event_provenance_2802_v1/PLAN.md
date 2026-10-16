# #2802 application-event provenance / clock-domain rung

Allocation: `app-event-provenance-2802-20260923-01`.

## H
For an ordered temporal obligation, numeric timestamps alone are insufficient. A `B` event must share the declared source and clock domain and arrive on a contiguous increasing source sequence. Cross-domain, gapped, regressed, or cross-source evidence must remain UNKNOWN rather than being laundered into ordered success. A true same-source/clock/contiguous `B` within 20 ms should satisfy; a late one should expire.

## T
Standard-library Linux process experiment. Six scenarios × three cyclic repetitions = 18 fresh child processes. Each child emits an application-like JSON event stream over its actual stdout pipe and performs a private file-state transition READY→DONE before `B`. Timestamps are actual `clock_gettime_ns` values from `CLOCK_MONOTONIC` or `CLOCK_BOOTTIME`. Candidate receives only event fields; final state is scoring-only. One formal invocation, no retry/replacement/tuning.

Scenarios: SAME_DOMAIN_CONTIGUOUS, CROSS_DOMAIN, GAPPED_SEQUENCE, REGRESSED_SEQUENCE, CROSS_SOURCE, LATE_B. Bound 20 ms; late sleep 40 ms.

## D
`PASS_APP_EVENT_PROVENANCE_BOUNDARY_SCOPED` iff all 18 rows and child exits/effects are complete; candidate yields SATISFIED3, EXPIRED3, and 3 each of UNKNOWN_CLOCK_DOMAIN/UNKNOWN_GAP/UNKNOWN_ORDER/UNKNOWN_SOURCE; the timestamp-only comparator produces unsupported SATISFIED in all 12 provenance-negative cases; independent audit errors=[]; all 12 corruption controls reject; source hashes remain frozen. Missing process/effect/raw/source evidence is STOP/HOLD. Complete unexpected semantics are FAIL/HOLD at the frozen gate.

## C
`CLOCK_MONOTONIC` and `CLOCK_BOOTTIME` are real Linux clocks, but this run does not suspend the host and does not estimate drift. The deliberately unsafe comparator is authored only as a control; no upstream production implementation is alleged. Stdout preserves one producer's byte-stream order but is not a distributed total-order service.

## U
No dropped transport bytes, reconnect, wrap, multiple simultaneous obligations, malicious producer, cross-host clock synchronization, GUI/model usefulness, token/latency benefit, task success, input authority, production runtime promotion or natural failure rate.
