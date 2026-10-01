# Local servo review projection — 2026-09-13

Candidate presentation_v3 projects only known local pointer_servo programs differently.
During those steps it suppresses ordinary same-context observation envelopes, local
pointer admissions/yields and correct-only servo progress. Full source events must
still be archived. Context/focus transitions, non-correction servo feedback, outcomes,
terminals, cancellation, rejection and unknown events remain forwarded. Terminal
review receipts retain the latest historical image reference and local outcome.

Manual pointer_guided yields retain their observation/reply flow. Ordinary keyboard
and other programs keep the preceding projection behavior. This candidate does not
add authority, refresh observations, stop archival captures or provide acknowledged
event retention. It is an optional lossy presentation, not a new control ABI.

## Matched trace results

`probe_servo_projection.py` feeds identical frozen source traces to presentation_v2
and presentation_v3, verifies input immutability, exact terminal receipt equality,
named critical-event forwarding and unchanged manual-guided output.

| Trace | Receipt JSON bytes | Local-review JSON bytes | Observation envelopes |
|---|---:|---:|---|
| Actual recovery 02 | 35,130 | 24,785 | 12 → 8 |
| Yield timeout | 5,609 | 2,876 | 2 → 1 |
| False visual goal / replacement | 15,382 | 10,796 | 6 → 4 |
| Manual guided assistant timeout | 15,401 | 15,401 | 5 → 5 |

These are serialized UTF-8 JSON sizes and envelope counts. The experiment does not
measure model-visible image count, tokens, cognitive cost or end-to-end latency.
The false visual goal remains visible as a local outcome and semantic verification
is still not implied. Source files, projection sources and projected outputs are
retained with hashes in results/servo-projection-01.

## Limits and next gate

Replay cannot prove live callback timing or transport behavior. In particular,
suppression changes how much time synchronous emission consumes. There is no live
model-in-loop evidence for this projection yet and no default entrypoint change.
Unknown-event forwarding is not a guarantee of semantic-event detection or delivery
acknowledgment. An important pixel-only change that produces no explicit event can
be hidden between terminal receipts; no durable event channel has been implemented.

Under Issue #12 this is DEVELOPMENT_KNOWN trace evaluation, not fresh/held-out task
success. Under Issue #11 it changes presentation, not the meaning of accepted,
terminal, local goal, semantic verification or task success. Next test live execution
and fresh cases containing unexpected visual events before selecting a default.
No token saving, latency speedup, critical-event retention qualification or freeze
credit follows from this replay.
