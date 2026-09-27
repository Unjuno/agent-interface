# Local visual continuation barrier v1

## Question

The rejected prompt receipt showed that another model interpretation can add
tokens and make progression more conservative. This candidate instead places an
agent-authored visual condition between steps of one already admitted program.
The condition cannot grant input authority: it can only allow or stop later
steps that were validated against the original fresh observation.

## Contract and archived calibration

`local_visual_barrier_v1.py` accepts an exact bounded contract: source sequence,
ROI, RGB threshold, minimum persistent pixels, two to five samples, sampling
interval, timeout and mandatory `needs_decision` behavior on failure. Binding
change, invalid frame, timeout and unmet conditions all stop. The program layer
requires each unique barrier immediately after a mutation and before another
mutation, and limits combined barrier time to3,000ms.

On the same posthoc selected OpenTTD frames used for the earlier receipt, the
pure evaluator passes nine first effects and stops two repeated completed-segment
drags, one transient control, binding change and timeout. The existing Executor
then continues a fake later input only for the met case and stops it for unmet
and changed-binding cases. These are boundary checks, not held-out correctness.

## Fresh X11 result

Two preliminary allocations are retained. Allocation01 fails before input
because `session_v23` assumed a binding helper from a different inheritance
line. Allocation02 repairs the integration, completes the three-step program and
then fails its independent displacement assertion.

Allocation03 records both fresh scripted Inkscape cases. In the nominal met
case, a requested24px drag produces only a12px final red-object displacement.
The single-ROI threshold nevertheless sees163 persistent changed pixels, marks
the barrier met and starts the later Save step. In the unmet case it sees zero
persistent pixels, returns `needs_decision`, verifies input release and never
starts Save. Seven exact reconstructed frames support the two cases.

| Endpoint | Met case | Unmet case |
| --- | ---: | ---: |
| persistent changed pixels | 163 | 0 |
| requested / final x displacement | 24 / 12px | n/a |
| later Save step started | yes | no |
| terminal | completed | needs_decision |
| release verified | yes | yes |

## Decision

Reject a single-ROI changed-pixel threshold as a continuation barrier. It detects
that something persisted, but the fresh X11 case demonstrates that it can admit
a partial unintended effect. Keep the measurement as advisory evidence only.

The next contract must express a task-relative visual postcondition. For a moved
object that can be target displacement. For placement, it needs separate target
and guard regions or another visual structure that can distinguish complete from
partial effect. Any condition still remains below independent task scoring.

No model benefit, task correctness, speed, token saving or generality follows.

Primary evidence:

- `results/local-visual-barrier-v1-probe.json`
- `results/local-visual-barrier-program-v1-probe.json`
- `results/local-visual-barrier-x11-01/failure.json`
- `results/local-visual-barrier-x11-02/failure.json`
- `results/local-visual-barrier-x11-03/report.json`
- `results/local-visual-barrier-x11-03/audit.json`
