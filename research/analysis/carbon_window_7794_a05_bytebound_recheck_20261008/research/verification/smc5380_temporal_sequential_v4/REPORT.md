# Issue #5380 T0-v4 — FORMAL-01

## Result

**PASS_SMC_METHOD_CALIBRATION_SCOPED.** The frozen gates passed on the declared synthetic IID generator. This is a method calibration only, not a safety-probability estimate for agent-interface or any deployed system.

## Evidence

- Construction suite: 9/9 passed on host CPython 3.11.9.
- Fixed replay: 100 traces, 1 observed violation.
- Weighted-uniform comparator: 1,000 traces, 14 observed violations (1.4%; Wilson 95% interval 0.84%–2.34%). Descriptive only under its frozen fault weights.
- Stratified sequential test: 245 samples total; four null strata accepted H0, and correlated-verifier reached FAIL after 3 samples with 2 retained counterexample seeds.
- Calibration at p0=.01: 55/2,000 false FAIL (2.75%); Wilson 95% interval 2.12%–3.56%, no inconclusive runs.
- Calibration at p1=.08: 1,796/2,000 detections (89.8%); Wilson 95% interval 88.40%–91.05%, no inconclusive runs.
- Independent pre-frozen auditor: integrity PASS, errors []. Recomputed 100 fixed, 1,000 uniform, 5 sequential strata, and 4,000 calibration replications.
- All 21 observed counterexample seeds were retained in the raw result.

## H / T / D / C / U decision

- **H:** Supported only for the fixed IID generator and injected rates: the per-stratum Wald test distinguished p0=.01 from p1=.08 at the frozen calibration thresholds and surfaced the high-risk correlated-verifier stratum.
- **T:** Compared fixed 20-per-stratum replay, 1,000 weighted-uniform traces, and one sequential SPRT per stratum with alpha=.05, beta=.10, max 500; deadline-bounded temporal property checked on simulated traces.
- **D:** PASS for all preregistered method gates: null Wilson upper <=.08, alternative Wilson lower >=.85, inconclusive limits, correlated-verifier FAIL, full seed retention, and independent audit with zero errors.
- **C:** If deployment faults are non-IID, adversarial, or have unknown weights, use bounded/adversarial search or conditional stratum reporting instead of extrapolating this test.
- **U:** Synthetic data only; no runtime, model, tool, OS, GUI, user input, or actual action was exercised. No real-world rate, rare-event, non-IID, multiplicity-adjusted, or universal safety guarantee. Five-stratum multiplicity is not corrected.

## Reproduction and environment

Formal runner was executed once from exact GitHub-readback sources using host CPython 3.11.9 (win32), python -B, with source streamed in memory and no local result files. container:false; Docker was not used because repository coordination Issue #5085 bars Docker CLI use pending resource release/allocation. GPU/model/network/action side effects: zero. LM Studio was stopped as unused before this run.

The initial construction attempt's single floating-point test failure remains unmodified at [CONSTRUCTION-01.json](CONSTRUCTION-01.json); the tolerance-corrected suite passed 9/9 before formal execution. Full raw evidence and independent audit are retained alongside this report.
