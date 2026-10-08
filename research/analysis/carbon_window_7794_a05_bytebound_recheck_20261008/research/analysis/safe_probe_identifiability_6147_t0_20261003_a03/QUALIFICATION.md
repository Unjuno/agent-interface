# Post-run qualification — frozen D gate not met

The first candidate and first raw-only auditor invocations are preserved in
`RUN_RECORD.json`; neither was rerun. The auditor exited 0 and printed
`PASS_METHOD_SCOPED`, with `mutation_controls_rejected: 5`. Reviewing the exact
frozen `auditor.py` after that call showed a mismatch between this summary and
the implemented mutation checks:

- The selected policy was asserted to use a probe in the hard-coded safe
  alphabet, and the string `u` was asserted absent from it.
- The auditor did **not** mutate a valid policy to use `u` and pass that policy
  through `valid_policy_shape` to demonstrate rejection.
- The other four corruption controls were exercised: dropped output branch,
  fabricated singleton under aliasing, non-closed bisimulation, and same-image
  recapture claiming identification.

The frozen D criterion explicitly required every one of the five corruptions
to be rejected. Therefore the emitted auditor PASS does not satisfy D. The
qualified allocation disposition is `FAIL_AUDIT_CONTROL_COVERAGE`; no
`PASS_METHOD_SCOPED` claim is made. The candidate's raw tree enumeration and
the auditor's independent reconstruction remain preserved scoped evidence, but
this control-coverage miss prevents the preregistered method PASS.

This is not repaired in place: the source was frozen and both formal invocations
were consumed. No code was changed or rerun. Any later attempt must use a new
prospective successor allocation, independently freeze a corrected validator,
and retain this qualification and both first outcomes unchanged.
