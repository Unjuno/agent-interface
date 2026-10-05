# Issue #7993 repeated-cohort IPCW — exploratory A01

**Disposition: EXPLORATORY_ONLY; formal T0 STOP before container execution.**

This is a separate continuation of Issue #7993's explicitly untested repeated-cohort/superpopulation estimand. It does not duplicate A01's finite assigned-cohort method result in PR #8028 and does not complete #7993.

## Question and exact scope

For independently generated cohorts with known, positive follow-up probabilities conditional on observed stratum X, does the design-weighted Horvitz–Thompson mean average to the known superpopulation risk across repeated cohorts, and can complete-case calibration be biased when outcome prevalence and follow-up probability both vary by X?

The authored population has two equally sized strata: P(Y=1|X=0)=0.40 and P(Y=1|X=1)=0.10, so marginal risk is 0.25. Follow-up is independent of Y conditional on X, with known pi(X=0)=0.25 and pi(X=1)=0.75. Each generated cohort has N=400. Seed 7993001 generated 20,000 cohorts. The reported HT point estimate is not a finite-sample guarantee or risk certificate.

Analytically, the complete-case large-sample target is [0.5*0.40*0.25 + 0.5*0.10*0.75] / [0.5*0.25 + 0.5*0.75] = 0.175, while E[(1/N) sum_i R_i Y_i / pi(X_i)] = E[Y] = 0.25 under the declared known-propensity design. The empirical numbers below agree with these expectations; they are not themselves proof of a calibration guarantee.

## Chronology / protocol status

The host calculation was exploratory and executed before a preregistration/freeze was committed. The result therefore cannot satisfy the Issue's formal frozen T/D gate, regardless of its numerical appearance. The exact source used and seed are preserved here; no threshold or endpoint was tuned after observing a formal result because no formal run occurred.

Important construction limitation: the script stores oracle_y beside observed fields in the same in-memory row objects and computes aggregate estimates directly; it is not a separated candidate process plus raw-only independent auditor. The observational-equivalence and positivity dispositions are authored diagnostic metadata, not decisions produced by a tested candidate. Thus this run does not satisfy the Issue's candidate/oracle-separation or UNKNOWN-control gates.

## Observed exploratory output

- Complete-case repeated-cohort mean: 0.1747974581 (bias -0.0752025419 vs 0.25).
- HT repeated-cohort mean: 0.2502748333 (bias +0.0002748333 vs 0.25).
- Mean realized cohort risk: 0.2498465000.
- Mean HT minus realized finite-cohort risk: +0.0004283333.
- HT between-cohort SD: 0.0445805578; complete-case SD: 0.0265216605.
- HT Monte Carlo standard error of the 20,000-cohort mean, estimated as SD/sqrt(20,000): approximately 0.000315; no interval or inferential gate was preregistered.
- Mean observed rows: 200.09565 / 400.
- Diagnostic observational-equivalence pair has equal visible fields and differing hidden-world outcomes; no candidate implementation tested it.
- Diagnostic positivity failure pi(X=0)=0 is labelled UNKNOWN in output metadata; no candidate implementation tested that response.

## Environment and validation limits

Executed on macOS host Python 3.14.5 using the standard library. No container ran. The current task directory is not a Git checkout. Read-only checks found an OrbStack Docker client/server, but docker ps / targeted docker image inspect failed on the same containerd content-blob operation-not-supported error. No inventory repair, image pull, prune, daemon restart, or VM change was attempted. WSLc is not installed/on PATH. No exact CPU/container assignment for this separate continuation was identified in the coordination evidence inspected; none is inferred from the completed #8028 run. Per current-goal macOS guidance, an eligible OrbStack alternative still needs usable pinned-image identity and collision/resource clearance; those gates were not established. Formal container execution and separate raw-only audit remain NOT RUN / STOP, not PASS.

The repository-side experiment code is included for transparent replay, but this PR is a method note / exploratory artifact only. It must not be described as the frozen formal A02. Any future formal attempt requires a fresh, source/hash-frozen allocation, exact estimator target and uncertainty treatment, isolated candidate-visible input, independent raw-only auditor, informative-delay/zero-support UNKNOWN gates, and an eligible container/runtime. Preserve this result as history; do not overwrite it.

## Limitations

The result only checks an authored, known propensity design in a simple synthetic generator. HT can have high variance, and this one seeded set of 20,000 repetitions does not establish a confidence interval, finite-sample risk control, estimated-propensity behavior, robustness to model misspecification, or transfer to verifier labels/GUI effects. The MC average's proximity to 0.25 is descriptive, not a statistical PASS.