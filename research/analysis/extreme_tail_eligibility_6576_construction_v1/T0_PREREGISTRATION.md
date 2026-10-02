# Issue #6576 T0 preregistration (OrbStack, one-shot)

Status: preparation only. Do not invoke the formal candidate or auditor until
the exact #5085 OrbStack allocation is assigned and the current-main/source/
image/output freeze is recorded. No formal rows exist yet.

## H / T / D / C / U

- **H:** A fail-closed eligibility gate will refuse unsupported synthetic
  extreme-tail claims (declared but absent mode, mode-count insufficiency,
  drift, dependence, or censoring), while allowing a sufficiently sampled
  stationary light-tail reference. Whether it improves held-out calibration
  over empirical p95/max, pooled EVT, and TailID is unknown.
- **T:** In one pinned CPU-only OrbStack container, generate 4,000 training
  and 4,000 independent held-out rows per frozen scenario, with fixed seeds.
  Compare empirical p95/max, pooled naive GPD p99, eligibility-gated analysis,
  and the source-backed TailID algorithmic comparator. The deliberately naive
  comparators consume every reported endpoint and treat a censor-limit value
  as if it were an observed endpoint; the eligibility gate must refuse such
  training input, and any censored holdout makes comparator calibration
  `NOT_ESTIMABLE_CENSORED_HOLDOUT`. Score p99 held-out exceedances (with exact
  binomial intervals), estimate availability/NOT_ESTIMABLE and false
  eligibility on negative controls. Include a declared cleanup mode absent
  from training but present in held-out deployment; do not claim detection of
  an undeclared mode.
- **D:** `PASS_METHOD_SCOPED` only if stationary reference is eligible, every
  invalid synthetic control is refused with its typed reason, no censored
  row is silently treated as on-time, and the frozen coverage interval
  includes the nominal 1% held-out exceedance rate for every eligible p99
  estimate. Any false eligibility or silent censor conversion is
  `FAIL_METHOD`. If the Python TailID comparator fails its internal validity
  checks or crashes, retain that outcome and mark comparator coverage
  incomplete; do not replace it after formal invocation.
- **C:** This is synthetic CPU method evidence only. Forty tail observations
  per mode is a frozen fixture eligibility threshold, not a statistically
  justified minimum. The TailID comparator is a source-backed Python
  algorithmic equivalent, not numerically cross-validated against CRAN/R;
  that limitation must appear in the report.
- **U:** No physical release samples, real stationarity, causal dependence
  mechanism, arbitrary unseen-mode detection, safety deadline protection,
  production false-alarm rate, or worst-case bound is tested.

## Frozen cases and gates

Seeds: `65761001` through `65761006`. Training/held-out sizes: 4,000 each,
generated from separate PRNG streams. Scenarios: (1) stationary exponential
reference (scale 1); (2) declared two-mode mixture (95% normal exponential
scale 1, 5% cleanup exponential scale 8); (3) time drift (first half scale 1,
second half scale 3); (4) clustered extremes (stationary base plus seeded
contiguous 20-row scale-12 bursts); (5) informative right censoring at 3.5,
with censor probability increasing with latent delay; (6) declared-but-unseen
cleanup mode absent in training and present at 5% in held-out deployment.

Eligibility prerequisites: exact endpoint identity, declared/observed mode
equality, at least 40 observed threshold exceedances per declared mode,
block-median stationarity ratio <=1.5, lag-1 exceedance-indicator correlation
<=0.10, and zero censored/missing endpoint rows. Unknown diagnostics refuse;
they never default to eligible. The count threshold does not establish
independence; dependence is a separate finite-fixture diagnostic. Gate
thresholds are finite-fixture controls, not universal inferential cutoffs.

For each eligible mode-specific p99 prediction, score held-out exceedances
against the two-sided 95% Clopper-Pearson interval for its uncensored
Binomial(n_mode, p=0.01) holdout; also report the pooled interval and exact
counts. The gated analysis stratifies by declared mode; naive EVT and TailID
remain explicitly unstratified comparators. Do not convert these finite checks
to safety assurance. Keep raw generated rows, seeds, source/image digests,
candidate stdout/stderr/exit, and independent raw-only audit output. Candidate
once, auditor once only if candidate exit=0, retries=0. Do not rerun or repair
the formal allocation after invocation.

## Container start gate

Use cached `python:3.12-slim` linux/arm64 image digest
`sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`,
`--pull=never`, `--network=none`, read-only source, unique writable output,
CPU-only limits, and record effective host cgroup/swap settings. Start only
after an exact exclusive allocation assignment. If assigned to the shared
Engine, also require explicit owner release of `unjuno-native-ci-6092`. If
assigned to a dedicated isolated OrbStack machine, record and verify that
machine's exact Docker daemon endpoint/identity and resource limits; do not
reuse another Issue's machine. This document alone is not a lease.
