# Post-run integrity review

The preregistered fixture specifies a saturated-input cap of `1/2` and includes a `capped_hold` policy row. The retained `candidate.json` records that row's first input as `-6/5`, violating the cap. This is directly visible in the unchanged raw output and frozen source (`simulate("capped_hold")` is called without `bounded=True`).

The separate auditor's independent reference also omits saturation for `capped_hold`, then compares the candidate to that same erroneous reference. Its five corruption probes therefore do not cover this protocol invariant. `audit.json` is preserved verbatim with its generated `PASS_AUDIT_METHOD_SCOPED` label, but that label is superseded for package-level disposition by this source/raw review: `FAIL_METHOD_T0; FAIL_AUDIT_COVERAGE_GAP`.

No script or raw output was changed after the one-shot candidate and auditor. No rerun, repair, alternate arm, or second audit was performed. The narrow exact recurrence/algebra values remain descriptive of the authored recurrence only; they do not rescue the frozen multi-arm T0 decision gate.

