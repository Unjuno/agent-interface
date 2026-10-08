# Issue #6195 delay–gain T0 — terminal method failure retained

One candidate and one separate raw-only auditor ran on the frozen finite scalar fixture (host CPU, CPython 3.11.9; no GPU, container, network, model, GUI, or physical input). The exact fresh and one-step-delayed algebra controls reproduced, but post-run review found that the `capped_hold` arm emitted `-6/5` against the frozen `1/2` input cap. The independent auditor copied the same missing-saturation behavior and accepted it.

Final disposition: **`FAIL_METHOD_T0; FAIL_AUDIT_COVERAGE_GAP`**. Preserve the generated `PASS_AUDIT_METHOD_SCOPED` raw label as historical output, not the package-level conclusion. Candidate/audit outputs remain unchanged; no retry or repair run was made. See [the full scoped result](outputs/DELAY-GAIN-STABILITY-6195-T0-HOST-20261001-01/RESULT.md), [post-run review](outputs/DELAY-GAIN-STABILITY-6195-T0-HOST-20261001-01/POST_RUN_REVIEW.md), [freeze](FREEZE.json), and [preregistration](PREREGISTRATION.md).

