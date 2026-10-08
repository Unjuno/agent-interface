# Issue #8522 T0 A02 — anchored ordinal calibration identifiability

**Successor allocation:** `ANCHORING-VIGNETTE-8522-T0-A02-20261009`. A01's `STOP_CANDIDATE_ENTRYPOINT_PATH` is preserved as a consumed allocation and is not rerun. This A02 repeats the same frozen scientific fixture under a fresh allocation, with an explicit repository-rooted CLI integration control and formal runner. It changes no scientific input or decision threshold from A01.

## H / T / D / C / U

**H.** A conventional ordered-logit anchoring-vignette calibration can recover a planted condition contrast when group response thresholds differ and vignette equivalence/response consistency hold. A uniform group shift in vignette latent meaning is observationally interchangeable with a response-threshold shift. If those worlds produce identical observed ratings but different self-rating contrasts, ratings alone cannot validate calibration assumptions; the proper disposition is `NOT_IDENTIFIED`.

**T.** A finite exact-probability fixture uses five ordinal categories, four fixed anchor levels, logistic errors, and two groups. The candidate estimates each group's threshold-location shift from anchor category probabilities by a frozen one-dimensional grid likelihood, then estimates self-rating locations conditional on that shift. A nonuniform vignette-shift case tests an observable model-fit diagnostic. An independently implemented raw-only auditor reconstructs both fits and the observational-equivalence witness. No human observations, model, GUI, runtime, or external service is involved.

**D.** The conditional method qualifies only if the assumed-world contrast is recovered within 0.002, detectable nonuniform anchor misfit is rejected, and the auditor verifies byte-identical observations for two worlds with distinct true contrasts. If all checks pass, the overall calibration conclusion remains `HOLD_NOT_IDENTIFIED`: the alias prevents identifying the assumption from the ratings alone. Any mismatch is `FAIL_AUDIT`.

**C.** An independent criterion, cognitive probe, or defensible external sensitivity bound could distinguish or bound alias worlds. A procedure that abstains on every dataset avoids false calibration but does not recover a usable contrast from ratings alone.

**U.** This exact finite logistic fixture tests algebraic identifiability, not finite-sample estimator performance, realistic vignette equivalence, human response consistency, psychometric validity, accessibility, or GUI workload. No human-data or route-comparison claim follows.

## Frozen model and controls

Categories are 1–5. Base cutpoints are `[-1.5, -0.5, 0.5, 1.5]`; logistic CDF is `1/(1+exp(-x))`; category probabilities are differences of adjacent cumulative probabilities. Anchor levels are `[-1.2, -0.4, 0.4, 1.2]`. Threshold shift is searched on `[-1.0,1.0]` at 0.001 increments; self location on `[-2.0,2.0]` at 0.001 increments; ties choose the lowest grid value. Maximum per-anchor probability residual above 0.01 rejects the common-anchor fit.

The assumption-satisfied world has threshold shifts `(0.0, 0.6)`, common anchor levels, and self locations `(-0.2, 0.4)`, so the true contrast is 0.6. Its observational alias has both shifts 0.0, comparison-group anchor levels shifted uniformly by -0.6, and comparison self location -0.2, so its true contrast is 0.0. Every ordered-logit argument is preserved. A nonuniform-vignette fixture uses comparison anchor offsets `[-0.5,-0.2,0.2,0.5]` and must exceed the residual threshold.

Four construction tests cover conditional recovery, detectable misfit, independent reconstruction, and exact observational equivalence. A fifth integration test invokes the frozen candidate and auditor CLIs from repository root using absolute package paths and temporary outputs; these pre-freeze invocations are construction checks, not the formal allocation. Formal runner `run_formal.sh` derives its repository root from its own location, records each command once, never retries, and invokes the auditor only after a successful candidate output exists.

## Formal execution and preservation

After the source/input/oracle and runner are frozen and preregistered, execute `run_formal.sh` once. Keep its stdout/stderr, exit codes, UTC timestamps, generated candidate/audit JSON, and hashes unchanged. Candidate and independent auditor each have one formal invocation maximum; retry budget is zero. A01 remains in its original branch/package with its first STOP intact.
