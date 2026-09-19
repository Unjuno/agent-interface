# Live pending-to-available status transition

The outcome client had been used by the assistant on its normal direct-result
path, but live pending status followed by a fresh available snapshot was still
unverified. This probe closes that specific gap using frozen socket v11/runtime
v27, outcome_fallback_v2 and test-only evaluator gating in private X11 xterm.

For correct and wrong tokens, the probe submits once and waits for terminal and
the evaluator waiting marker. The bounded helper first times out on the outcome
read and queries status, which is pending. Releasing the gate permits ordinary
evaluation. A read-only wait then receives the final evaluation. The probe
replays the exact old status request (including its old cursor); it receives
the identical pending snapshot with replayed=true and no new runtime query.

A new helper invocation starts after the consumed final evaluation. Its outcome
read times out, then its freshly generated status query receives available with
the retained true/false evaluation. This deliberately tests fallback recovery
from a consumed outcome event; it is not the preferred normal caller sequence.

| Case | Initial status | Exact old-query replay | Fresh query | Input submits |
|---|---|---|---|---:|
| Correct token | pending | same pending snapshot | available, success=true | 1 |
| Wrong token | pending | same pending snapshot | available, success=false | 1 |

Each helper invocation uses two exchanges. Exactly two status commands reach
the runtime per case; replay sends no third status command. Three exact AIT/PNG
frames per case, input release, request lineage, each returned prefix slice,
source hashes and saved token are verified. Both processes exit zero and remove
their socket paths. The wrong token's final evaluation is false, not unknown.

Evaluation gates were held 134.394 and 135.950 ms. Terminal-to-evaluation times
were 148.653 ms and 3157.001 ms; the failure includes the ordinary scorer's
roughly three-second mismatch polling. These are test-induced timings with no
model or human comparison. This is scripted fault injection, not assistant
self-use or a new benchmark domain. Original measured sources remain frozen.

The exact old request includes an old read cursor. Reusing its command ID with
a newer cursor does not promise to return its old snapshot: the command is still
not resent, so the scoped read may time out. Use a new query ID for a new sample,
preserve the furthest processed cursor across replays, and retain all returned
records. Session-local replay suppression is not a durable result cache.

Evidence: results/status-transition-01 and probe_status_transition.py, with
gated_evaluation_entry_v2.py and gated_socket_entry_v2.py. The next useful step
is a visible recovery decision in actual assistant use, rather than further
microbenchmarks of successful status snapshots. No default promotion or speedup
claim follows from this coverage test.
