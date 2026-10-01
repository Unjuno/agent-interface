# Managed reply process snapshot: task passed, no roundtrip reduction

The primary assistant used candidate source 794234b96 through one persistent
MCP relay connection in a fresh WSL Inkscape allocation, seed 991123, max stages
2. Initial public context included the restored directional task description.
The assistant viewed three returned images and authored two action submissions;
both immutable requests are byte-identical to the previous combined-source
trial. The initial frame hash also matches that trial.

The first action returned a valid stage 2 / sequence 7 continuation and a ready
process snapshot. The final action saved X=74, Y=50, width=40, height=30 and
returned evaluation success and cleanup completed. The exact X is an observed
value, not the directional task's unique target.

The final allocation snapshot was needs_review with owner.state=terminal and
no returncode. NativeAllocation first polls its child, then reads owner state;
this is consistent with exit becoming visible between those reads. The raw
evidence does not timestamp each read and cannot establish the exact ordering.
The assistant therefore made one explicit native_status request on the same
owner, obtaining PID 19706 terminal, exit 0. Relay session 71141 then exited 0
on EOF. There was no retry, restart, or corrective GUI input.

This candidate did not reduce roundtrips in this trial: start + two submits +
one status, the same as the previous trial. Preserve this negative utility
result. Successful task completion does not establish performance benefit.
Another usability issue is retained: the ready snapshot's source_stage=1 is
startup metadata, while continuation.stage=2 describes the next action. It
must not be interpreted as a new stage-1 action instruction.

Run `python audit.py` for retained-file hashes, three image payloads, matching
requests, continuation linkage, input releases, saved geometry, the unresolved
final process snapshot and subsequent terminal status. This audit was written
by the same assistant, not an independent reviewer. The manifest covers every
retained file except itself. It verifies evidence, not a new application run.
Docker was not used; issue #3352 remains unmet. Host presentation time, model
token/cost, human baseline and causal latency effects remain unmeasured.
