# Allocation 7993-T0-A02 — exact IPCW expectation subgate

## Relationship to existing evidence

PR #8028 records A01's formal finite-cohort bounds and label-maturity method result. PR #8034 records an exploratory, non-preregistered Monte Carlo estimate over 20,000 cohorts, without an independent raw auditor. This A02 tests only the still-open superpopulation-estimator subgate: exact inverse-probability weighting under the declared independent-censoring model, exhaustively audited over the full small design. It imports no prior raw rows or outputs and does not repeat A01's cohort-bound comparison.

## H — hypothesis

For the fixed four-unit design below, the candidate's uncapped inverse-probability-weighted estimate has exact expectation equal to the known superpopulation risk when label resolution is independent of the binary error outcome within each declared stratum and every resolution probability is positive. With zero support, the candidate returns `UNKNOWN_NONPOSITIVITY` and no numeric estimator.

## T — one-shot exact enumeration

Fix four covariate strata `A,A,B,B`. In the auditor-only design, error probabilities are `p_A=1/4` and `p_B=3/4`, so the design's expected risk is `(1/4 + 1/4 + 3/4 + 3/4)/4 = 1/2`. Label resolution is declared independent of error conditional on stratum, with `q_A=1/2` and `q_B=1`. Enumerate all `2^4=16` binary error vectors and all `2^2=4` resolution masks for the two A rows, giving 64 disjoint joint outcomes. B rows always resolve. Each case has an exact rational probability weight; the candidate sees only stratum, q, resolution status, and resolved error labels, never p or unresolved outcomes.

For each observed case the candidate computes the uncapped Horvitz–Thompson value `R_hat = (1/N) * Σ_i Δ_i Y_i / q_{s(i)}` and labels it strictly as an assumption-conditional **superpopulation expected-risk estimator**. It emits no finite-cohort point claim. A separate zero-support negative control uses `q_A=0` and must return `UNKNOWN_NONPOSITIVITY` with no numeric value.

The independent raw-only auditor recomputes the complete 64-state support, each exact probability weight, each observed-case estimator, total probability mass, the weighted estimator expectation, the true design risk, the zero-support disposition, and six frozen output mutations. No Monte Carlo draws or asymptotic confidence claims are used.

## Environment and explicit delta

Read-only OrbStack image inventory failed with `containerd ... operation not supported` on a stored blob. No image was pulled, no container was created or started, and no existing container was changed. A02 therefore prospectively uses native macOS CPython 3.14.5, standard library only, in one low-priority, one-shot driver. This is **not** a container-isolation result and does not claim OS-enforced network isolation. The candidate and auditor make no network calls. No model, GUI, user data, GPU, or external effect is used.

## D — allocation-scoped decision

`PASS_METHOD_SCOPED` requires: the 64 states are exhaustive and disjoint; their independently recomputed exact weights sum to 1; the candidate's estimate for every visible state matches the independent formula; the exact weighted expectation is `1/2`, equal to the preregistered design risk; the estimate is never typed as realized finite-cohort risk; zero support returns `UNKNOWN` without a numeric estimate; and all six mutations are rejected. Any missing state, weight error, false numeric output, target conflation, or accepted mutation is `FAIL_METHOD`. This is only the IPCW estimator subgate for #7993, not a full Issue PASS or a live-calibration result.

## C — competing explanation

The prior exploratory Monte Carlo estimate may be numerically near the target by chance or due to a correct implementation; exact enumeration is useful here because the authored state space is small. If label resolution depends on error, the same estimator need not identify the target. If all labels mature, direct cohort counting is simpler.

## U — uncertainty

The strata, outcome rates, and resolution model are authored. The exact identity validates the estimator under the specified finite repeated-sampling design only. It does not estimate a real verifier risk, test informative censoring, provide a finite-sample coverage guarantee, validate conformal risk control, or support a production policy.

## Symbols

| Symbol | Meaning | SI unit | Range / assumption | Type |
|---|---|---|---|---|
| `N` | Fixed units in each enumerated cohort | `1` (count) | `N=4` | Integer |
| `Y_i` | Error indicator for unit `i` | `1` (dimensionless) | `0` or `1` | Boolean |
| `Δ_i` | Whether unit `i` resolved by checkpoint | `1` (dimensionless) | `0` or `1` | Boolean |
| `p_s` | Error probability in stratum `s` | `1` (dimensionless) | `p_A=1/4`, `p_B=3/4`; auditor-only | Rational |
| `q_s` | Resolution probability in stratum `s` | `1` (dimensionless) | `q_A=1/2`, `q_B=1`; candidate-visible | Rational |
| `R` | Design's superpopulation expected error risk | `1` (dimensionless) | `R=1/2` | Rational |
| `R_hat` | One cohort's HT estimator of `R` | `1` (dimensionless) | May exceed 1; never a finite-cohort bound | Rational |
