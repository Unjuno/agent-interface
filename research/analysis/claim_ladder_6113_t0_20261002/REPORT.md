# Issue #6113 T0 — scoped finite-method result

**Disposition: METHOD_PASS_SCOPED for these eight authored tables only.** No route-population equivalence, noninferiority, or product correctness claim follows.

## Results

The candidate and an independently structured raw-table auditor agreed with all eight frozen truth rows. The low-power equal-count fixture has exact paired McNemar `p=1`, yet the conservative correctness risk-difference interval is about `[-0.422, +0.422]`; it is therefore `NO_DETECTED_DIFFERENCE` and `UNRESOLVED_PRECISION`, not equivalence. The speed fixture has a separately bounded median-latency interval wholly below zero while its correctness interval still permits material loss, so the result is `BENEFIT_WITH_UNRESOLVED_CORRECTNESS`. The correctness fixture with 5 adverse and 0 favorable discordances has `p=0.0625`, a simultaneous conservative risk interval about `[-0.123, -0.066]`, passes only the deliberately larger synthetic NI margin 0.15, and fails the tighter two-sided equivalence margin 0.05. This illustrates the labels; it does not justify either margin for product correctness.

For the continuous soft-latency control, the exact order-statistic interval for the paired median is `[-1.2, 1.1] ms`, with distribution-free coverage `0.9921875` under the frozen i.i.d.-paired-unit assumption, inside the authored ±2 ms synthetic margin. Missing outcomes, changed task mix, posthoc margins, and any forbidden-effect event lead to typed HOLD/hard-gate failure regardless of favorable means. Construction mutations confirmed forbidden events override a large latency improvement and missingness overrides a posthoc margin.

## Method / scope

Binary paired correctness uses exact two-sided McNemar testing. Its simultaneous risk-difference interval is conservative: four one-sided Clopper–Pearson bounds (gain/loss, lower/upper), each tail alpha 0.0125 for 95% requested joint coverage, then interval subtraction. The union bound gives at least 95% simultaneous coverage without assuming independent route arms. The continuous endpoint uses a distribution-free order-statistic confidence interval for the paired median, requiring representative independent pairs and a stable endpoint. The fixtures cannot establish these sampling assumptions.

The “difference-only” anti-pattern is represented explicitly: when its p-value does not reject, a promotion to equivalence is tagged false. A hard forbidden event is not folded into an average or an epsilon. All data and margins are authored controls, not measurements.

## Execution and integrity

- Frozen source base: `abd0ce6425e24934731b763ece83421d309535b5`.
- Candidate `candidate.py` invoked once and independent auditor `audit.py` invoked once with the frozen `public.json`; both exited 0.
- Raw stdout is retained in `candidate.raw.json` and `audit.raw.json`; SHA-256 values are recorded in `RUN.json` and `SHA256SUMS`.
- Construction tests were separate and passed before freeze: candidate/auditor/truth agreement 8/8 plus forbidden-effect and missingness mutation controls.
- Host CPython was used. Docker Engine was unavailable in this session; no shared backend restart and no container-isolation claim.
- No model/provider, network experiment, GUI, app/game, GPU, or physical input was used.

## H/T/D/C/U

- **H:** The eight controls separate no-difference detection from interval-qualified claims and preserve hard/missingness gates.
- **T:** Eight finite paired outcome tables; exact McNemar, simultaneous conservative paired risk bounds, exact median order-statistic interval; candidate plus raw-only independent audit.
- **D:** `METHOD_PASS_SCOPED` on the fixture only; no population or route claim.
- **C:** Descriptive results plus exact hard correctness gates may be preferable where any correctness-loss margin is unacceptable.
- **U:** Margins, cohort, missingness, and endpoints are stipulated; no prospective task sample, scorer calibration, route trial, or power justification exists.
