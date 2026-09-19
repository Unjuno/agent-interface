# A9 result — fresh real-X11 temporal-ring Rung1 integration

Decision: **PASS_X11_TEMPORAL_RING_RUNG1_INTEGRATION_SCOPED**

A9 is the fresh coordination-valid successor to #1084. It preserves #1084's scientific contract exactly while using a new Issue, branch, namespace, displays and formal identity. #1084 rows are not pooled.

## Primary result
- 24/24 ring historical requests; extra acquisition boundaries: 0
- ring request→evidence p95: 29.530 µs
- 24/24 JIT live-only requests; acquisition boundaries: 24
- JIT request→future-equivalent evidence median: 100.485 ms
- paired median JIT-minus-ring: 100.485 ms
- future-equivalent evidence promoted as historical: 0
- input authority grants: 0

## Capture integrity
Exact ROI [80,60,160,120], exact 76,800-byte normalized payload, zero capture exceptions. Ring capture p95 ranged 0.451–0.700 ms; JIT p95 0.419–0.666 ms. Maximum historical target offset error was 1.319 ms, below the frozen 35 ms gate.

## Coordination integrity
Reservation was committed before source publication. The branch and Issue were reread after source freeze and again after the formal run; no foreign write or comment was observed. Formal invocation=1, reruns/replacements/tuning=0.

## Scope
This closes only the real-X11 acquisition-boundary question for the declared private live-only source. It does not show that temporal history improves model decisions, task correctness, tokens, or a replay-capable/production capture backend.
