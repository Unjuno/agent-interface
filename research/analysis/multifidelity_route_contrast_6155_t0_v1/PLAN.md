# Issue #6155 T0 — route-contrast covariance eligibility

## H / T / D / C / U

- **H:** A multi-fidelity control variate should be admitted for a candidate-vs-baseline cost contrast only when its signed coefficient is fit on independent pilot *within-task differences* `ΔY=Y_candidate−Y_baseline` and `ΔX=X_candidate−X_baseline`. High correlation between arm-level `Y` and `X` caused only by a shared task component must not produce a gain claim. Genuine positive and negative `Corr(ΔY,ΔX)` may both help when the coefficient is signed.
- **T:** Seeded synthetic finite simulation with a large shared task-level component; compare (a) shared-level-only / independent differences, (b) predictive positive difference covariance, and (c) predictive negative difference covariance. Freeze a pilot independent of scored units, a predeclared amortization grid, total-cost-matched Y-only control, and audit of both level and difference correlations. No GUI, model, network, or product route.
- **D:** `PASS_METHOD_SCOPED` only if the shared-level-only arm has high arm-level correlation but approximately zero difference correlation, selects no material coefficient, and shows no cost-adjusted gain; both signed predictive controls must produce independently audited cost-matched MSE reduction without pilot/scored leakage. Otherwise preserve `FAIL`/`NO_GAIN`/`HOLD` by arm; no aggregate masking.
- **C:** Gaussian synthetic population, shared task component, cost ratio, pilot size, and finite Monte Carlo seeds are stipulated, not calibrated to real tasks. The target is the mean paired route-cost difference; the low-fidelity value is never an outcome or safety score.
- **U:** This method check does not establish real-app covariance, representativeness, task quality, safety, or model/runtime benefit. A later T1 needs independently frozen same-task real high-fidelity differences and measured costs. No real route or model is exercised here.

## Collision and execution boundary

Successor to #6155's host-only T0c and its explicit route-difference eligibility note (#5937007984); does not change those results. New branch/path and unique allocation only. Formal candidate and separate raw-only auditor are intended to run once each in distinct, network-disabled containers from the cached `python:3.12-slim` linux/arm64 image digest `sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`. The shared OrbStack lane is currently occupied; no container may be launched until an exact exclusive allocation is granted and a fresh start gate passes. Host construction checks are not formal evidence.

## Freeze status

Preparation only. Formal seed/source freeze, candidate, auditor, and allocation outputs are intentionally not yet established. Do not interpret this plan or host tests as an experiment result.
