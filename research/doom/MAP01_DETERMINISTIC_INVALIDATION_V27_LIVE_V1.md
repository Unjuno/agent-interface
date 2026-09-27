# Frozen deterministic MAP01 invalidation composition

The preregistered v27 allocation ran a real continuously advancing MAP01 game
and one persistent Luna-low planner thread for two decisions.  Decision zero
received the test-only invalidation on the fourth exact observation after its
source frame, at sequence 5.  The record explicitly identifies an injected
event, claims no semantic visual change, and grants no input authority.

The controller sent the matching planner interrupt 0.025 ms after detecting the
event.  Interrupt acknowledgment arrived 2.192 ms after send and interrupted
completion arrived after 3.279 ms.  Cover zero reached verified empty release
24.057 ms after detection.  No decision-zero plan was admitted, its answer was
ineligible, and no `next_cover` survived.

Decision one then reused the same planner thread with a distinct turn ID.  It
started from sequence 5 with empty cover and no source iteration, completed a
schema-valid forward action, and its plan released cleanly.  All three admitted
programs in the run have verified empty key/button release.  The first turn had
no usage notification and remains unknown; the second reported 9,357 input
tokens, including 7,936 cached, plus 282 output and 197 reasoning tokens.

This is the missing controller-level composition evidence: exact observation,
typed planner cancellation, local cover release, stale action rejection, and
fresh same-thread recovery work in one live process.  It is an injected
construction event, so it is not evidence about natural visual classification,
gameplay quality, reliability, or saved tokens.

The injection arguments should now be removed from normal runs.  More DOOM
allocations are not the highest-value next step.  The persistent typed boundary
should transfer to the shared desktop acquisition/golden path, where the same
tasks can compare correctness, model wait, cache/input accounting, round trips,
and recovery against its retained per-process bridge.  That transfer tests
whether this is a shared Agent Interface improvement rather than an FPS-only
mechanism.
