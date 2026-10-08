# A01 formal result — `FAIL_METHOD`

Frozen base: main `0c9bf746a8bb07564cde3d0c3283af6aff942be0`. Executed on local Windows CPU with Python 3.12.10; no container, WSLc, model, GUI, GPU, network, or human responses. The candidate and its independent auditor each ran once.

The candidate emitted all five predeclared fixture classes: F01 `COMPATIBLE_SCREEN`, F02 `THRESHOLD_NONINVARIANCE` localized to item 2, F03 `LOADING_PATTERN_NONINVARIANCE` localized to item 2, F04 `STRUCTURE_NONINVARIANCE`, and F05 `UNCERTAIN`. These are candidate outputs, not an accepted method result.

The A01 auditor returned `FAIL_METHOD` with `classification_mismatch:F02`, `independent_reason_mismatch:F02`, and `independent_threshold_items_mismatch:F02`. The first outcome is retained unchanged. Post-run source diagnosis: the auditor took the maximum cumulative proportion separately in each group and then subtracted those maxima. The frozen gate requires the maximum *per-cutpoint between-group difference*. The candidate formula was correct for the planted F02 cutpoint; the A01 auditor formula was not.

The distinct A02 audit-only package preserves A01 and independently recomputes the saved bytes, but A02 also ends `FAIL_AUDIT_ONLY` because its own README source digest was frozen incorrectly. Its reconstructed class map and mutation checks are descriptive diagnostics only; neither failure is relabeled or promoted to PASS.

## Disposition and limits

Overall Issue #8502 T0 is **inconclusive / no `METHOD_PASS_SCOPED`**. Preserve both failures. Do not rerun A01, patch its auditor, or infer anything about human workload, measurement invariance, latent-mean comparability, accessibility, route benefit, or Agent Interface safety. A future audit would need a genuinely new, prospectively frozen allocation; no such allocation is started here.

On a clean checkout, reproduce the recorded first outcomes in order with `python research/analysis/measurement_invariance_8502_t0_a01_20261008/generate.py`, then `python research/analysis/measurement_invariance_8502_t0_a01_20261008/candidate.py`, then `python research/analysis/measurement_invariance_8502_t0_a01_20261008/audit.py`; generation and output use exclusive creation. The A02 audit-only invocation is documented in that package's README. The source, fixtures, candidate JSON, failed A01 audit, and failed A02 audit remain beside their freeze manifests.
