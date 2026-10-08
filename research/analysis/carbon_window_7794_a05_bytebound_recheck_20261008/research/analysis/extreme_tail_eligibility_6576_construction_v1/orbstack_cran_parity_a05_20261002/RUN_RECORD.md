# A05 run record — numerical parity gate failed

**Disposition:** `FAIL_PARITY_NUMERICAL_MLE`; candidate invocation 1, both
arms exit 0; independent raw-only audit invocation 1, exit 1; retries 0.

The auditor evaluated all six fresh 400-row stationary exponential fixtures.
Exact candidate indices/order, raw-only order-statistic selection, threshold
within 1e-10, exact sensitive-index sets (after normalizing scalar/list JSON
encoding), and all R optimizer convergence codes passed. Five fixtures passed
all compared cumulative MLE/CI states. The remaining fixture, seed 65769925,
failed only at the frozen base-fit tolerances:

- R `ismev::gpd.fit`: scale `2.0058689679563897`, shape `-1.0319603276768672`,
  CI `[-1.6832690288812515, -0.38065162647248285]`.
- Python port: scale `2.0098104420228644`, shape `-1.0339880996470936`, CI
  `[-1.6865766034687355, -0.3813995958254516]`.
- Relative scale difference `0.00196497086` > `0.001`; absolute shape
  difference `0.00202777197` > `0.001`; max CI endpoint difference
  `0.00330757459` > `0.002`.

Conclusion is narrow: on these six synthetic fixtures, the Python port
reproduced the selected/sensitive indices and thresholds, but did not satisfy
the preregistered numerical MLE/CI parity gate on one base fit. Do not use this
Python port as an R-numerically-equivalent comparator at these tolerances
without further work. This does not show statistical inferiority, estimator
bias, physical endpoint validity, safety, or performance effects. No candidate
or auditor was rerun or patched after invocation.

All frozen source, inputs, raw JSON, stdout/stderr, exit codes and auditor
diagnostics are retained here and enumerated in `SHA256SUMS`.
