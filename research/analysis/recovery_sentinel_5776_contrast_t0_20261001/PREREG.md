# Preregistration — Issue #5776 contrast T0

Allocation `recovery-sentinel-5776-contrast-t0-20261001-01`; fresh successor experiment, not pooled with v1/v2.

## H / T / D / C / U

- **H:** Under fixed repeated perturbations in this synthetic event system, the final/first recovery-duration ratio gives at least 0.25 higher held-out sensitivity for future gradual-recovery losses than pointwise margin warnings, while both methods remain within the same ≤0.10 false-alarm budget in each load stratum and target warnings lead loss by at least four ticks.
- **T:** Candidate creates all 3×7×32 prospective episodes (load strata × mechanisms × episode IDs) and 100 raw event rows per episode. Episodes 0–15 are a reference partition; 16–31 are the fixed held-out partition. No parameter or threshold is fitted on either partition: the probe ticks, statistic and thresholds are fixed in `fixture.json`. Candidate and raw-only event-replay auditor are separately invoked once each in separate network-disabled Docker containers. No model, GUI, external service or live task.
- **D:** Audit must reconstruct every state transition, shock schedule, service event, envelope return, warning lead time and outcome with zero mismatch. Only then `PASS_METHOD_SCOPED` if gradual-loss sensitivity ≥0.75, incremental sensitivity over pointwise margin ≥0.25, both methods' false-alarm rate ≤0.10 in every held-out load stratum, and minimum target-warning lead ≥4 ticks. Otherwise `FAIL_METHOD_SCOPED`; any identity/replay mismatch is `FAIL_INTEGRITY`. Abrupt and spontaneous loss cases are retained as positive controls without assuming a slowing precursor. Unknown endpoints remain excluded from denominators and reported.
- **C:** Demand drift may mimic slow recovery; a pointwise margin may itself fully explain or outperform a response statistic; abrupt failures may have no gradual precursor.
- **U:** The deterministic fixture is authored and repetitive, with no sampled deployment prevalence. Rates describe only its held-out rows. No Agent Interface telemetry, predictive utility, live causal effect, safety, or product claim.

## Frozen execution plan

Base main at freeze: `1548fc9c556a8a690c40ad30e6dd604c3754bf94`. Exact Linux image manifest digest/platform and guest identity are recorded in `FREEZE.json` before formal execution. Candidate command: `python -B /src/research/analysis/recovery_sentinel_5776_contrast_t0_20261001/runner.py /out/raw.json`; independent auditor command: `python -B /src/research/analysis/recovery_sentinel_5776_contrast_t0_20261001/audit.py /out/raw.json`.

No formal candidate or auditor invocation has been made at preregistration. Host construction tests are not the experimental result. No formal invocation occurs until an explicit isolated OrbStack slot is granted and fresh source/image/hash gates pass.
