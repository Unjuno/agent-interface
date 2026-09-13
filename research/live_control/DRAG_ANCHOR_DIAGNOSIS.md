# Drag anchor diagnosis and bounded visual correction

The installed application reports Inkscape 1.2.2 (b0a8486541). Its release source
checks drag tolerance and initializes the selection transform at the first
qualifying motion point before moving it. This suggests a start-anchor effect,
not proof that the final event was lost. See the official
[1.2.2 selection tool source, motion handler](https://gitlab.com/inkscape/inkscape/-/raw/INKSCAPE_1_2_2/src/ui/tools/select-tool.cpp),
around lines 468–542. The current generated documentation was also inspected but
the release source is the relevant reference. No Inkscape internals were patched.

Two new scripted diagnostic arms captured the rectangle while Button1 remained
held. Each capture followed a separate owner input-state sample and a 150 ms wait.
These added captures perturb timing; this is not a speed comparison or tracing of
the application's received event queue. Both arms used the same explicit shared
owner10/executor5 candidate and fresh seed-214 fixture.

| Phase | Physical pointer x | Red rectangle right edge |
|---|---:|---:|
| Pressed | 618 | 642 |
| First coarse motion | 628 | 642 |
| End motion | 638 | 652 |
| Released | 638 | 652 |

The second arm inserted x=619 before x=628. The rectangle still did not move until
the subsequent x=638 motion; both saved x=58.474575 and failed the declared x=66.95
target. Thus a one-pixel initial segment did not fix the task. The owner sample
confirmed each requested coordinate and physical Button1 state. This supports a
qualifying-motion anchor explanation and contradicts attributing the result only
to insufficient final dwell. Exact internal causality/threshold was not instrumented.
Two recent temporary preferences files showed dragtolerance=4, but their paths
were not recorded in these arm manifests; do not treat that read as pinned evidence
of the arms' exact settings.

## One feedback correction reaches the saved target

`trace_drag_feedback_v2.py` ran one diagnostic arm. From the held image, its declared
canvas-only red-object sensor measured a 10-pixel residual to a target right edge
20 pixels beyond the pressed phase. With matching y/size, it permitted at most one
horizontal correction of at most 12 pixels. It queried current input state, then
used the same owner's ordinary guarded move under the original lease. The pointer
moved from x=638 to x=648; observed right edge became 662. After release and save,
the independent SVG score passed x=66.94915, y=50, width=40, height=30, no transform.
The assistant inspected the final original image after this scripted run.

This is a task-specific diagnostic controller, not model-driven in-flight control
or a generic primitive. Its backend subclass inserts captures and a correction
outside the public prevalidated path semantics; the fixed script bounds and owner
checks are not a complete public validation contract. It therefore must not become
the shared API merely because this case passed. No automatic fixed offset should
be added to ordinary pointer_drag.

## Reuse existing research

Bounded feedback is already developed in [DRAG_FEEDBACK.md](DRAG_FEEDBACK.md),
[SERVO_INTERFACE.md](SERVO_INTERFACE.md), and [SERVO_TRIM.md](SERVO_TRIM.md), including
planner-selected patches, outcome mapping and distractor limits. The present red
sensor is diagnostic evidence for the recent legacy-session path, not a replacement
or new general capability. Next reconcile the new cause/wake executor with those
existing validated continuation/servo candidates and use independent saved-task
scoring. Do not restart a separate servo implementation from this probe.

## Evidence and execution failure

`results/drag-anchor-01/` retains both failed diagnostic arms.
`results/cause-drag-feedback-01/` retains the corrected arm and
`audit_drag_anchor_v1.py` output. The auditor recomputes all phase red bounds,
checks pointer/button samples, listed source hashes, saved scores, terminal
release verification and all 46 exact frames. Samples precede captures and are
not atomic proof that a button remains down during image delivery. Source manifests
are not exhaustive environment manifests. All three arm cleanup calls returned;
no independent per-child process inventory is claimed.

The first feedback launch (`trace_drag_feedback_v1.py`) failed at exclusive mkdir
because `results/drag-feedback-01` already held older research. It started no app,
did not modify that evidence, and was not retried in place. Version 2 uses a distinct
result directory. That startup failure is retained with the unused version-1 source.
No model token/cost, end-to-end speed, formal benchmark or Research Freeze claim.
