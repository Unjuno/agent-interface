# X11 relevant-region coordinate-frame move boundary

Issue: #4439. Allocation: `x11-region-frame-move-q5t2-20260926-01`.

This directory is an additive research fixture. It compares a pinned initial
screen rectangle, a freshly translated screen rectangle, and direct
`window_client` capture for a fixed target-relative region while the same X11
window moves. It grants no input/replay/task-success authority.

Formal execution is forbidden until every file in `FREEZE.json` plus the freeze
itself has been published and read back exactly from the owned branch. The
excluded construction is not pooled with formal results. Two auditor
construction defects were retained before the final audit rejected 12/12
well-formed evidence mutations.

Formal plan: 3 policies x 3 schedules x 3 fresh repetitions = 27 sessions in
three immutable 9-case batches. See `PLAN.json` and Issue #4439 for H/T/D/C/U.
