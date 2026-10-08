# Issue #6155 T0e — route-contrast covariance eligibility

## H / T / D / C / U

- **H:** A multifidelity control variate for a candidate-vs-baseline cost contrast should be selected from independent pilot covariance of within-task differences `ΔY` and `ΔX`. Large arm-level `Y`/`X` correlation caused only by shared task difficulty must not create a gain claim. Signed positive and negative difference covariance may both help.
- **T:** 3 synthetic cases × K={1,5,20} × 300 independent seeded blocks = 2,700 raw records. Each block includes a 64-pair independent pilot, per scored cohort 20 paired `(ΔY,ΔX)` rows and 80 X-only rows, plus a Y-only comparator charged the entire pilot+scored cost. One candidate, then one separate raw-only auditor; retries=0.
- **D:** Frozen acceptance gate required exact pilot-inclusive cost equality and independent reconstruction of all rows; the shared-level control needed high arm-level correlation but no difference-level gain; both signed predictive controls needed ≥5% cost-matched MSE reduction with Bonferroni family-wise 95% intervals below zero at K=20. Overall disposition is `FAIL_METHOD_GATE` because the positive-difference arm's interval crosses zero. The raw/audit accounting checks passed; the positive control did not meet its inferential gate.
- **C:** Hand-specified Gaussian synthetic population, shared task component, cost ratio, seed schedule, and Monte Carlo design; not calibrated against actual GUI tasks, model costs, or an application route.
- **U:** This is not real GUI/model/task, safety, correctness, runtime, or product evidence. It neither validates nor refutes real-world multifidelity usefulness. X is not a substitute for an independently scored high-fidelity effect or a safety endpoint.

## Execution and audit

The frozen source ran in two distinct `linux/arm64` OrbStack containers from `python:3.12-slim@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`. Both were CPU-limited to one CPU, memory-limited to 1 GiB, network-disabled, read-only rootfs, capability-dropped, and automatically removed on exit. Candidate source was mounted read-only. The auditor received source and raw data read-only and a separate audit output mount. The pre-existing `unjuno-native-ci-6092` container was only seen in inventory and left untouched. This execution was directly user-directed; no #5085 lease is claimed.

Candidate: exit 0; 2,700 JSONL records. Independent auditor: exit 1, 9 groups / 2,700 rows reconstructed, exactly one decision-gate error:

`delta_positive: predictive signed-difference control did not show audited >=5% gain`

At K=20:

| Case | Mean arm-level Corr(Y,X) | Mean Corr(ΔY,ΔX) | Mean pilot β | CV MSE reduction vs cost-matched Y-only | Family-wise 95% CI for MSE(CV)−MSE(Y-only) | Gate |
|---|---:|---:|---:|---:|---:|---|
| Shared-level-only | 0.9899 | -0.0009 | 0.0018 | -4.61% | [-0.000568, 0.000763] | Pass negative control: high levels, no difference signal, no resolved gain |
| Positive Δ covariance | 0.9979 | 0.8005 | 0.8043 | 21.08% | [-0.000861, 0.000116] | Fail gate: point gain, interval crosses zero |
| Negative Δ covariance | 0.9821 | -0.7990 | -0.8002 | 30.76% | [-0.001253, -0.000077] | Pass signed negative control |

The positive arm's point estimate exceeds the 5% criterion, but its family-wise interval is not wholly below zero; it is unresolved under the frozen decision rule, not a confirmed gain. The other K results remain in the independent audit JSON; no threshold or case was selected post hoc. The shared-level negative control behaved as specified: arm levels were highly correlated, while the within-task differences and fitted coefficient were near zero. The negative covariance arm also shows why coefficient sign must not be constrained to positive.

## Cost/accounting gate

One paired high/low unit costs 101, one low-only unit costs 1, and one high-only comparator unit costs 100. Every record independently reconstructs identical total cost for the two estimators: 8,564 (K=1), 16,964 (K=5), or 48,464 (K=20), including the 64-pair coefficient pilot. The auditor checked all row counts, finite values, arm-minus-baseline arithmetic, deterministic block set, and the nine case/K groups. The one audit error is solely the preregistered positive-control inferential gate.

## Interpretation / next step

Retain this allocation unchanged as `FAIL_METHOD_GATE`; do not rerun it or weaken its interval gate. The scoped evidence supports the eligibility distinction in this synthetic fixture and shows a clear signed-negative gain, but the positive arm is statistically unresolved at this allocation. A larger independently seeded successor may be worthwhile only as a separately preregistered allocation; no real-world conclusion follows. Full run commands, return codes, byte counts, and digests are in [RUN.md](runs/MULTIFIDELITY-ROUTE-CONTRAST-6155-T0-20261002-01/RUN.md).
