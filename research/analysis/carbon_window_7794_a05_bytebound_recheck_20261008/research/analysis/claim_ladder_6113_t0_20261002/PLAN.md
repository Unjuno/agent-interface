# Issue #6113 T0 — claim ladder for route comparisons

## H / T / D / C / U

- **H:** The claim ladder refuses low-precision and posthoc “no significant difference means same” promotions while permitting only the particular predeclared endpoint claims supported by their intervals, and a forbidden-effect event always blocks a positive route claim.
- **T:** Eight deterministic authored table cases. For paired binary correctness, use exact two-sided McNemar discordance p-values plus conservative paired risk-difference bounds built from two one-sided Clopper–Pearson bounds with Bonferroni family coverage. For a soft continuous endpoint, use the exact distribution-free order-statistic interval for the paired median. Reconstruct with a separately implemented auditor. No model, GUI, external route, or allocation.
- **D:** `METHOD_PASS_SCOPED` only if low-power identical observations yield NO_DETECTED_DIFFERENCE but not equivalence; interval-supported noninferiority is distinct from two-sided equivalence; continuous endpoint equivalence is granted only when its interval is within the frozen margin; missingness, task-mixture drift, posthoc margins HOLD; and a forbidden event blocks regardless of benefit. Candidate/auditor/truth must agree.
- **C:** Descriptive counts plus exact correctness gates may suffice where no loss margin is ethically or scientifically justified; then correctness remains unresolved absent a zero-loss proof.
- **U:** Authored tables, chosen margins, synthetic missingness and effect flags; no target population, statistical power plan, route sample, oracle calibration, or product claim is established.

## Method boundary

Schuirmann’s TOST comparison is an equivalence-testing paper in bioavailability; it supports the distinction between testing a null of no difference and testing whether an interval falls inside a prespecified equivalence region, not any Agent Interface margin. FDA’s non-inferiority guidance likewise emphasizes interpretable design and justified margins in clinical trials; it does not authorize correctness loss here. This T0 treats a positive correctness margin only as a synthetic test control and never proposes it for product acceptance.

The binary paired interval is intentionally conservative: use four one-sided Clopper–Pearson bounds (gain/loss lower/upper), each with tail alpha 0.0125 for a 95% requested joint level, then subtract the component intervals. The union bound gives at least 95% simultaneous coverage, without pretending independent route samples. The continuous median interval is distribution-free only under independent representative paired units and a stable continuous endpoint. The fixtures cannot validate those assumptions.

Primary sources: Schuirmann (1987), [DOI](https://doi.org/10.1007/BF01068419); FDA (2016), [Non-Inferiority Clinical Trials to Establish Effectiveness](https://www.fda.gov/media/78504/download?attachment=).

## Execution boundary

Frozen source base `4526e4b19b6addebca5b498a8047f25929d39846`; additive package path only. Run construction controls before formal freeze; one candidate and one independent auditor invocation after output-absence check. Host CPython is sufficient. Docker Engine was already unresponsive in this session; do not restart the shared backend and make no container-isolation claim. No provider/model, network experiment, GUI, app, game, GPU, or physical input.
