# MAP01 persistent planner controller v26

V26 is the first construction version that joins v25's exact event-driven
observation monitor to the official typed app-server interruption boundary.
The frozen v25 controller and all earlier evidence remain unchanged.

One capability-minimized app-server process stays alive for the run.  A planner
thread remains stable for the configured session span, while every decision has
its own turn ID.  The temporal sheet is passed as a local image and the existing
MAP01 v3 action schema is supplied to app-server.  Adapter v2 independently
checks types, strict fields, enums, constants, array/string bounds, uniqueness,
and numeric ranges before the existing semantic action checks run.

When the health ROI changes or becomes unknown, v26 marks the matching planner
turn stale and sends one typed interrupt before cancelling the current local
cover.  It then waits for planner terminal completion and the cover terminal
release independently.  The action, including its proposed `next_cover`, is
recorded as ineligible and receives no plan admission.  If the planner had
already completed when the event arrived, the interrupt reports
`already_terminal`, but the changed observation still discards that answer.

The report records thread and turn identity, server turn status, cancellation
request, interrupt outcome, answer eligibility, usage availability, cover
terminal, and stale-action disposition as separate fields.  A missing partial
usage notification remains unknown.

Nineteen adapter tests and three v26 boundary tests pass.  A WSL command-free
initialization diagnostic reaches the Windows Codex Desktop 0.153.4 app-server.
Two earlier diagnostic attempts are retained as harness failures: nested shell
quoting broke the first, and the second omitted the repository root from
Python's module path while a cleanup command masked the WSL exit status.

No live DOOM run has used v26 yet.  Freeze a small integration allocation first;
its acceptance must require typed planner completion for every started turn,
verified release for every admitted cover, zero plan admission from invalidated
turns, and no inherited cover from those turns.  Gameplay improvement is a
separate question.
