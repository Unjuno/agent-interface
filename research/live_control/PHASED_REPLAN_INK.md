# Live target activation followed by a checked keyboard phase

phased_replan_ink_v1.py runs the existing response-loss / same-window selection
fault episode through socket_v8 and executor_v9, with an explicit two-phase
caller. Initial X88 edit and fault remain scripted. The model subsequently
selects the rectangle, proposes X104, and verifies visible geometry.

The first click plus observe uses the unchanged pixel-contract deadline
(capture + one second). A keyboard tail is allowed only after completed
activation, resolved durable state, and a clock/observe/clock exchange that
passes activation_handoff_v1. The new keyboard-only program gets a distinct
action ID and an explicit two-second deadline from that clock. It does not
renew the activation lease. Interrupted activation or a refused handoff stops
the driver without replay. This is an opt-in experiment, not a generic caller
API or proof of semantic widget identity.

One fresh live episode completed both phases and independently saved
X104/Y50/W40/H30. Activation completed 449.892ms before its deadline; the
keyboard program (Ctrl+A, text104, Return, Ctrl+S, observe) completed
1374.590ms before its separate deadline. Handoff clock/observe/clock took
315.835ms. All runtime program terminals completed with verified empty input
release. The final screenshot visibly agrees with the parsed SVG.

Audit replays 173 events, 27 exact frame/PNG pairs, 55 journal records and 27
durable exchanges. It verifies source hashes, model image/prompt/response
provenance, original lost-command reconciliation without replay, both pixel
checks and handoff against recorded observations, distinct phase IDs, exact
model-tail preservation, admission deadlines, successful process exit, removed
sockets and independent SVG geometry. Evidence: results/phased-replan-ink-01;
replay with audit_phased_replan_ink_v1.py under Linux.

Four model calls consumed 44,988 input tokens (22,528 cached) and 691 output
tokens. Runner times were 10.701, 6.964, 10.864 and 7.644 seconds. Initial capture
to independent evaluation was 42.083 seconds. The prior unphased episode took
40.960 seconds and saved the same artifact while its last program expired;
these single episodes have varying model/cache timings and are not a causal
speed comparison. The result supports separating target freshness from input
duration, not overall speed improvement. Actual cost remains unavailable.

Open work: failure injection at the inter-phase boundary, tighter integration
to remove the extra round trips without weakening evidence, general caller
extraction, and validation on a different desktop interaction/domain. Repeating
this one coordinate task cannot establish human-like live performance. Same
surface/focus/pointer samples still cannot prove same-window widget identity or
atomicity between sample and input.
