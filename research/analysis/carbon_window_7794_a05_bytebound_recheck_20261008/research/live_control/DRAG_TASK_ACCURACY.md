# Selected-object drag: two failed displacement checks

Two explicit self-use episodes used Inkscape seed 214 and the unchanged
cause_session_v1/input_owner_v10/executor_v5 runtime. The assistant reviewed each
initial image, clicked the rectangle, reviewed its selected state (x=50,y=50,
width=40,height=30), then dragged and saved. All six selected images and the
decision_receipt_v3 outputs were visible. Initial and selected PNG hashes match
between episodes. Each used six socket exchanges and eleven exact frames.

Before the first action, the plan declared a 20-screen-pixel horizontal drag at
118% zoom: expected saved x=66.95 +/-1, y=50 +/-0.1, width=40 and height=30 +/-0.1.
This task target is explicit and distinct from the inherited random goal.dx field,
which the legacy interactive task does not require precisely.

| Episode | Program path, total 600 ms | Saved x | Declared task |
|---|---|---:|---|
| drag-live-01 | (618,391) → (628,391) → (638,391) | 58.474575 | fail |
| drag-live-02 | same path plus duplicate (638,391), adding 200 ms at endpoint within the same total | 58.474575 | fail |

Both preserved y=50, width=40, height=30, without transforms. Saved SVGs are
byte-identical. Both reported all input steps completed and the legacy independent
evaluator reported success because it only requires movement to the right. Neither
is a success for the declared displacement. `score_drag_v1.py` checks the saved
rectangle against the numeric target and fails both. It refuses transformed or
unsupported rectangle structure; it is a fixture geometry oracle, not full SVG
equivalence. The scorer was implemented after the first run using its predeclared
target, then pinned before the second run.

The first image suggested only an intermediate displacement was reflected. A
bounded endpoint dwell was tested as an exploratory hypothesis, not silently added
to the default drag primitive. It did not solve the discrepancy and is not adopted.
The second path changes intermediate segment timing and repeats a motion as well
as adding dwell; it is not a pure one-variable timing experiment. These outcomes
do not prove that the last event was lost or establish an application root cause.

## Consequences and next evidence

Input acknowledgement, terminal completion, and pixel quiet cannot establish the
requested drag displacement. Keep the stricter saved-output check for subsequent
precision tasks; do not reinterpret the older coarse benchmark's successes as
precision successes. The receipt correctly says task success is unknown even when
it has no attention flags. No generic interface fix follows from a guessed delay.

Next inspect or instrument the actual motion events and application response at
the start/intermediate/end of a selected-object drag. Separate drag threshold or
anchor behavior from event delivery and release timing before choosing another
candidate. Retain the negative baseline and failed dwell experiment. A corrected
primitive still needs explicit cancellation/focus guards and validation on another
GUI domain before promotion.

## Audit

`audit_drag_live_v1.py` verifies pinned sources, raw socket-to-runtime event slices,
receipt reconstruction, 89 events and 22 exact frames across the two episodes,
matching initial/selected pixels, verified input cleanup, and both strict saved
scores. `results/drag-live-02/paired-audit.json` summarizes evidence. The outer bridge
handles each returned exit 0; inherited cleanup has no independent per-process
inventory. Capture-to-evaluation was 61.235823274 and 69.604031187 seconds, including
model inspection/commentary. Neither model token/cost accounting nor human-speed
qualification is available. Both task failures remain archived.
