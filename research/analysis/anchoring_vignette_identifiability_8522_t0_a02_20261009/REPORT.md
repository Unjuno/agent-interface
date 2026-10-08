# Issue #8522 T0 A02 result

**Scoped result:** `PASS_METHOD_SCOPED` for conditional ordered-logit recovery and detectable nonuniform-anchor misfit; `HOLD_NOT_IDENTIFIED` for calibrating the assumption from observed ratings. The frozen candidate and independent auditor each ran exactly once, both exited 0, and the auditor reported 12/12 checks with zero errors.

In the assumption-satisfied authored world, the candidate's conditional contrast was 0.6000000000000001 against truth 0.6, with maximum anchor residual about `5.6e-17`. In the nonuniform-vignette case, the comparison-group residual was 0.122636, above the frozen 0.01 gate, so the candidate rejected the fit. The auditor reconstructed both.

The auditor also verified that the assumption-satisfied world (threshold shifts 0.0/0.6, true contrast 0.6) and a uniform vignette-meaning-shift world (threshold shifts 0.0/0.0, true contrast 0.0) generate byte-identical observed input. Ratings alone therefore cannot distinguish assumption validity from the alias. All five frozen corruption controls were detected. Candidate input excluded auditor truth.

A01's `STOP_CANDIDATE_ENTRYPOINT_PATH` remains unchanged and separately preserved; this result is A02 under a new allocation. A02 added a pre-freeze repository-root CLI integration test, which exposed and allowed repair of a tuple/list comparison bug in the auditor before freeze. The scientific input and oracle hashes are identical to A01.

This exact-probability synthetic result does not establish finite-sample estimator performance, realistic human vignette equivalence or response consistency, workload validity, accessibility, GUI effects, or user/product benefit. No human ratings were collected.
