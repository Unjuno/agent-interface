# Persistent planner adapter v1

`persistent_planner_adapter_v1.py` separates one long-lived planner session
from individual observation turns.  One thread ID remains stable across turns;
session replacement is explicit and is refused while a turn is active.  Each
turn combines text, an optional local image, and an output schema under its own
typed turn ID.

The cancellation boundary is deliberately one-way.  The first interrupt marks
the observation stale before sending `turn/interrupt`.  Once marked, that
turn's answer is ineligible even if a completed response wins a protocol race
or the interrupt request itself returns an error.  A second interrupt sends no
request.  If completion is already terminal before interruption begins, the
adapter reports `already_terminal` and leaves the completed result eligible.

An answer is admitted only when all of these conditions hold:

- terminal status is `completed`;
- no cancellation was requested;
- exactly one completed agent message exists;
- its text parses as JSON;
- the parsed value passes the controller-side action schema subset.

The local validator covers strict objects, required and additional fields,
arrays, primitive types, and enums used by current action contracts.  Missing
usage remains `None`, meaning unavailable rather than zero.  An interrupted,
failed, missing, duplicate, malformed, or schema-invalid message cannot become
an action.

Nine deterministic protocol-double tests cover normal completion, both sides
of the completion/interrupt race, duplicate interruption, interrupted answers,
missing usage, malformed and ambiguous messages, stable session identity,
explicit reset, and overlapping-turn refusal.  The first package-mode test
attempt failed only because the test imported its sibling as a top-level
module; the package-qualified import fixes the harness and the same suite now
passes.

This is contract evidence, not a live planner-latency or controller result.
The next bounded live probe should send two structured turns through one
capability-minimized thread and verify thread continuity, exact turn ownership,
message eligibility, usage accounting, and process startup amortization.  A
separate later allocation can interrupt a genuinely in-flight generation.
