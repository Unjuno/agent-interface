# A02: retained screenshot target-handle replay

This offline experiment replays A14's frozen model-proposed field and Save coordinates through the actual A01 target-handle registry on the exact retained PNGs. The initial expected test found an input-oracle contradiction: A14's visual review called task 3 blank, but its pinned screenshot visibly includes the form and Save control. That hypothesis failure and its transcript are retained.

After reconciling the screenshot itself, all ten proposed points are visibly on the named controls. The 24×24 center-patch rule returns `VALID` for seven points and `FLAT_REFUSED` for the centers of three visibly present fields in tasks 4–6. Each refused field patch has channel standard deviation 0 and creates no registry entry. All five Save points and both left-layout field points resolve. No model, GUI, or input was used.

The evidence demonstrates a conservative false-negative coverage boundary for flat field interiors and identifies a contradictory upstream visual label. It does not prove semantic grounding, false-positive resistance, live target safety, task completion, or efficiency. See `PLAN.md`, `INPUTS.json`, `VISUAL_REVIEW.json`, `RESULT.json`, and `out/PREREGISTERED_EXPECTATION_FAILURE.txt`.
