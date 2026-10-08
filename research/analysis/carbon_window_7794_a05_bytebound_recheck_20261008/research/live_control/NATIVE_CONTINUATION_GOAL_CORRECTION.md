# Correction: native continuation trial's interpretation of dx

The retained `runtime/results/native-continuation-integrated-01` trial on source
0548066eb saved X=74, Y=50, width=40, height=30 and completed successfully. Those
measurements remain valid. Its README and provenance nevertheless interpreted
the exposed dx=24 as a precise SVG displacement target. That interpretation is
incorrect: dx is the fixture controller's nominal screen-space drag offset.

The inherited evaluator in `research/observation_gating/gui_suite.py` requires
one rectangle, no transform, X > 50.5, and absolute deviations below 0.1 from
Y=50, width=40 and height=30. It does not require X=74. The trial demonstrates
successful directional movement and continuation/terminal integration, not
exact target attainment implied by dx. Its strict X=74 audit proves the retained
file's value, not that 74 is the evaluator's unique acceptable value.

PR #3065 (merge 8576c0fd1d43aec861d0d7c9761c1a3bbc545caf) already exposed this
task contract in goal.task. That Inkscape branch is absent in source 0548066eb,
while the Calc task branch remains. Restore the descriptive Inkscape contract
before goal publication. Preserve the evaluator and archived run bytes; this
note corrects their interpretation without rewriting frozen evidence.

The missing task description caused a real primary-assistant misunderstanding.
Restoring it is an interface correctness repair. No speed, token savings or
reliability improvement follows from this correction alone.
