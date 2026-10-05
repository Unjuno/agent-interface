# Issue #7993 repeated-cohort IPCW — exploratory A01

**Disposition: EXPLORATORY_ONLY; formal T0 STOP before container execution.**

This is a separate continuation of Issue #7993's explicitly untested repeated-cohort/superpopulation estimand. It does not duplicate A01's finite assigned-cohort method result in PR #8028 and does not complete #7993.

## Question and exact scope

For independently generated cohorts with known, positive follow-up probabilities conditional on observed stratum X, does the design-weighted Horvitz–Thompson mean average to the known superpopulation risk across repeated cohorts, and can complete-case calibration be biased when outcome prevalence and follow-up probability both vary by X?

The authored population has two equally sized strata: P(Y=1|X=0)=0.40 and P(Y=1|X=1)=0.10, so marginal risk is 0.25. Follow-up is independent of Y conditional on X, with known pi(X=0)=0.25 and pi(X=1)=0.75. Each generated cohort has N=400. Seed 7993001 generated 20,000 cohorts. Candidate-visible rows omit Y when not followed up. The reported HT point estimate is not a finite-sample guarantee or risk certificate.

## Chronology / protocol status

The host calculation was exploratory and executed before a preregistration/freeze was committed. The result therefore cannot satisfy the Issue's formal frozen T/D gate, regardless of its numerical appearance. The exact source used and seed are preserved here; no threshold or endpoint was tuned after observing a formal result because no formal run occurred.

A deliberately observationally equivalent row pair has identical candidate-visible content but hidden-world risks 0 and 1. The candidate disposition is UNKNOWN absent a justified observation model. A zero-probability stratum is likewise marked UNKNOWN; no IPCW estimate is emitted for that case.

## Observed exploratory output

- Complete-case repeated-cohort mean: 0.1747974581 (bias -0.0752025419 vs 0.25).
- HT repeated-cohort mean: 0.2502748333 (bias +0.0002748333 vs 0.25).
- Mean realized cohort risk: 0.2498465000.
- Mean HT minus realized finite-cohort risk: +0.0004283333.
- HT between-cohort SD: 0.0445805578; complete-case SD: 0.0265216605.
- Mean observed rows: 200.09565 / 400.
- Observational-equivalence check: candidate-visible rows equal; hidden risks differ; UNKNOWN.
- Positivity failure case: pi(X=0)=0 -> UNKNOWN.

## Environment and validation limits

Executed on macOS host Python 3.14.5 using the standard library. No container ran. The current task directory is not a Git checkout; Docker client/server access did not succeed (docker version exited 128). Issue #5085 is a GPU coordination log, not a CPU lease; no CPU/container allocation was found or inferred. Accordingly the Issue-required pinned Dockerless WSLc formal execution and separate raw-only audit remain NOT RUN / STOP, not PASS.

The repository-side experiment code is included for transparent replay, but this PR is a method note / exploratory artifact only. It must not be described as the frozen formal A02. Any future formal attempt requires a fresh, source/hash-frozen allocation, exact estimator target and uncertainty treatment, independent raw-only auditor, candidate information-set separation, informative-delay/zero-support UNKNOWN gates, and the specified WSLc environment. Preserve this result as history; do not overwrite it.

## Limitations

The result only checks an authored, known propensity design in a simple synthetic generator. HT can have high variance, and this one seeded set of 20,000 repetitions does not establish a confidence interval, finite-sample risk control, estimated-propensity behavior, robustness to model misspecification, or transfer to verifier labels/GUI effects. The MC average's proximity to 0.25 is descriptive, not a statistical PASS.