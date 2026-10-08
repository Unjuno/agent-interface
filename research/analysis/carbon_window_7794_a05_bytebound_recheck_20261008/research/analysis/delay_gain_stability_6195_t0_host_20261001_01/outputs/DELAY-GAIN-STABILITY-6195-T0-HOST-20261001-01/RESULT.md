# Issue #6195 T0 — failed method implementation, audit gap retained

Allocation `DELAY-GAIN-STABILITY-6195-T0-HOST-20261001-01` ran once on Windows host CPU/Python 3.11.9 against frozen main `3d33fe482ad55e99943f2c7b40e92c685c3bf92a`. Candidate exit=0 at 19:05:32–19:05:35 UTC; separate raw-only auditor exit=0 at 19:05:40–19:05:43 UTC; retries=0. No container, model, GPU/CUDA, network, GUI, application, or physical input was used.

The exact algebra controls in the raw candidate are internally consistent: fresh pole `-1/5`; one-step-delayed characteristic `z^2-z+6/5`, root-modulus-squared `6/5`; the fresh and history-reconstructed traces match, while the naive delayed trajectory reaches the frozen forbidden magnitude at step 5. The 5 authored mutation probes were rejected by the auditor.

**Terminal result: `FAIL_METHOD_T0; FAIL_AUDIT_COVERAGE_GAP`.** Post-run raw review found the purported `capped_hold` trajectory applied `u[0]=-6/5` although the frozen input cap is `1/2`. The auditor independently reproduced the same row and failed to validate saturation, so its generated `PASS_AUDIT_METHOD_SCOPED` is not accepted as an overall audit pass. The original `candidate.json` and `audit.json` remain unchanged; the discrepancy is preserved in `POST_RUN_REVIEW.md` and `RUN.json`.

This is a finite authored scalar-method failure, not a GUI/DOOM/runtime result. It does not establish real-world instability or safety. No retry, corrected candidate, alternate gain, or replacement seed was run. A future attempt requires a distinct successor allocation and fresh preregistration.

