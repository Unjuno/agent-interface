# Human return-to-own-work resumption assay — Issue #6492

This package records the Issue's **T0 method-only** work and its immutable
allocation history. The original fixture contains six synthetic scenarios ×
four arms (24 rows), but the 24 rows are not one completed experiment:
allocations 01–03 stopped before candidate; allocation 04 stopped before
container creation; allocation 05 formally evaluated only the six
`immediate_modal` rows. Parallel PR #6499 independently tested three other
arms using a different fixture; do not pool those data as a matched comparison.

The four arms are immediate modal, timing-only, preserved source-bound view,
and preserved view with an optional user-authored cue. Questions, answer
choices/facts, task facts, interruption duration, task state and source identity
are matched within each scenario. Cases include cue written/unused, changed
state, a no-cue task, duplicate-effect risk, and urgent release.

## Run and limits

See `PREREGISTRATION.md` and each `results/allocation-*/` record for the
H/T/D/C/U, stops, exact commands and outcomes. Formal allocation 05 is
`PASS_METHOD_SCOPED` for the immediate-modal method fixture only. No
participant, personal data, GUI, model, actual interrupt, or effect was used.
This assay cannot establish human resumption accuracy, speed, burden, or benefit.
The primary cognitive-science sources are listed in Issue #6492; their reported
task effects are not transferred to Agent Interface.
