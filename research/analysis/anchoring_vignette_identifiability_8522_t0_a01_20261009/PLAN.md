# Issue #8522 T0 A01 — anchoring-vignette identifiability boundary

## H / T / D / C / U

**H.** A conventional ordered-logit anchoring-vignette calibration can recover a planted condition contrast when group response thresholds differ and vignette equivalence/response consistency hold. However, a uniform group shift in vignette latent meaning is observationally interchangeable with a response-threshold shift. If these worlds produce identical observed ratings but different self-rating contrasts, ratings alone cannot validate the calibration assumptions; the proper disposition is `NOT_IDENTIFIED`, not a calibrated claim.

**T.** A finite exact-probability fixture uses five ordinal categories, four fixed anchor levels, logistic errors, and two groups. The candidate estimates each group's threshold-location shift from anchor category probabilities by a frozen one-dimensional grid likelihood, then estimates group self-rating locations conditional on that shift. A second fixture applies nonuniform vignette shifts to test whether the model-fit diagnostic detects an observable violation. An independent raw-only auditor separately recomputes fits and constructs the observational-equivalence witness. No human observations, model, GUI, runtime, or external service is used.

**D.** `PASS_METHOD_SCOPED` for this boundary test only if the conditional estimator recovers the assumed-world contrast within 0.002, detects the nonuniform anchor violation and declines calibration, and the independent auditor proves that the assumed and uniform-violation worlds have byte-identical observed input but distinct true contrasts. The overall calibration conclusion is `HOLD_NOT_IDENTIFIED` if the alias is confirmed: a data-only diagnostic cannot tell which world generated those ratings. Any mutation mismatch is `FAIL_AUDIT`.

**C.** A separately validated criterion, cognitive probe, or defensible externally imposed sensitivity bound could distinguish or bound the alias worlds. A sufficiently conservative procedure could also abstain on every dataset; that avoids false calibration but does not recover a usable contrast from ratings alone.

**U.** This exact finite logistic fixture tests algebraic identifiability, not finite-sample estimator performance, realistic vignette equivalence, response consistency in human respondents, psychometric validity, accessibility, or GUI workload. No human-data or route-comparison claim follows.

## Frozen model

Categories are 1–5. Base cutpoints are `[-1.5, -0.5, 0.5, 1.5]`; logistic CDF is `1/(1+exp(-x))`; category probabilities follow the ordered-logit difference of adjacent cumulative probabilities. Anchor latent levels are `[-1.2, -0.4, 0.4, 1.2]`. The estimator searches threshold shift `b` on `[-1.0,1.0]` in increments of `0.001`, minimizing multinomial cross-entropy on anchors, then searches self latent location `mu` on `[-2.0,2.0]` in increments of `0.001`. Ties choose the lowest grid value. A maximum per-anchor category-probability residual above `0.01` rejects the common-anchor model.

The assumed world has group threshold shifts `(0.0, 0.6)`, common anchor levels, and self locations `(-0.2, 0.4)`, so the true contrast is `0.6`. The alias world has both threshold shifts `0.0`, comparison-group anchor levels shifted uniformly by `-0.6`, and comparison self location `-0.2`, so its true contrast is `0.0`. Since every ordered-logit argument `cutpoint + threshold_shift - latent_location` is preserved, all observable rating probabilities are exactly identical. A third, nonuniform-vignette fixture uses comparison-group anchor shifts `[-0.5,-0.2,0.2,0.5]` and must exceed the fit-residual threshold.

This package tests exact population probabilities, not sampled respondents or confidence intervals. Formal candidate and independent auditor each run once after freeze; no retries or pooling.

## Commands

```sh
python3.12 -m unittest discover -s research/analysis/anchoring_vignette_identifiability_8522_t0_a01_20261009 -p 'test_*.py'
python3.12 research/analysis/anchoring_vignette_identifiability_8522_t0_a01_20261009/candidate.py research/analysis/anchoring_vignette_identifiability_8522_t0_a01_20261009/candidate_input.json /tmp/8522-a01-candidate.json
python3.12 research/analysis/anchoring_vignette_identifiability_8522_t0_a01_20261009/auditor.py research/analysis/anchoring_vignette_identifiability_8522_t0_a01_20261009/candidate_input.json /tmp/8522-a01-candidate.json research/analysis/anchoring_vignette_identifiability_8522_t0_a01_20261009/oracle.json /tmp/8522-a01-audit.json
```
