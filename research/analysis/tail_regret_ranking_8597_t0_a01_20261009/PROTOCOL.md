# Issue #8597 T0 A01 protocol

## Scope and estimand

Finite synthetic method test only. Each assigned opportunity receives one per-opportunity endpoint in synthetic regret units with the #8528 scope boundary: opportunity-level aggregation only; #8528 defines within-window loss as a sum of 0/1 mismatch loss over open ticks and the admissible set. Its source/result anchor is commit `3f6bc41adaaf6dcc96ff0fd0deea5c691140c8d8`; this rank fixture supplies finite endpoint values and does not rerun or claim to derive #8528 tick losses. Route-level opportunity values are authored integers in [0,4], strictly synthetic. Hard safety violation is categorical and excluded from every scalar ranking.

Evaluation unit: 24 assigned opportunities, 12 in each of two prespecified strata S1/S2, grouped into six session clusters of four opportunities. All are fully observed and uncensored in this Issue #8597 T0. Session clusters are disclosed; no iid or population inference is made. A separate synthetic arm contains one extreme but explicitly out-of-scope benign score spike and is never pooled into the in-scope denominator. Missing-truth and unresolved/censored opportunities are retained as UNKNOWN/NOT SCORED and excluded from numeric estimands only with the denominator and count shown; this fixture includes one of each as separate assigned controls, so main cohort remains 24 scored opportunities plus controls.

Metrics, all exact finite summaries: pooled mean; macro mean (unweighted average of S1/S2 means); upper-tail ES20 defined as arithmetic mean of the largest ceil(0.20*n) opportunity losses (for n=24, top 5); per-stratum ES20 with ceil(0.20*n_stratum) (top 3 of 12); exceedance count/rate at loss >= 3 with explicit denominator. No confidence interval or population tail estimate is claimed. Cluster-aware descriptive check reports cluster means and a deterministic exact six-cluster delete-one range; it is not a calibrated inferential interval.

## H/T/D/C/U

- H: At least one matched route pair in this fixed finite fixture has equal/lower pooled mean but worse ES20; means can conceal a rare high-loss opportunity. Macro and stratum-tail outputs expose whether reversal survives strata. The out-of-scope spike, UNKNOWN/censored controls, and hard safety status remain separate.
- T: deterministic CPU-only Python standard library enumeration; 24 assigned opportunities, two strata, three routes, six clusters, plus three explicit controls. Candidate emits route-opportunity losses and summaries. Independent raw-only auditor reconstructs from sealed truth and frozen route actions/loss table, then recalculates every denominator and summary without importing candidate code.
- D: PASS_METHOD_SCOPED only if exact auditor equality holds; the preregistered primary pair A/B ties at pooled mean (A=0.5, B=0.5) while ES20 reverses (A=2.2, B=1.0), macro means and each stratum are reported (A/B macro mean 0.5/0.5; macro ES20 4/3 vs 0.5); all assigned in-scope opportunities are accounted once; controls stay separate; hard safety remains categorical and never enters utility; and all six mutation probes are rejected. FAIL_METHOD if a denominator drops/duplicates, route rank calculation is wrong, the primary contrast fails, or any safety/UNKNOWN/control collapse passes. HOLD if any #8528-compatible oracle/loss meaning is not reproducibly represented.
- C: A single extreme can dominate a small-sample ES; means may be sufficient after stratification; cluster composition can explain a pooled reversal; tail estimates are unstable at n=24.
- U: Authored finite values do not estimate real GUI-agent distributions, route quality, task value, causal effects, safety, or population tails. The top-5 mean and threshold are fixture diagnostics only. Session dependence is displayed but six clusters cannot calibrate uncertainty.

## Frozen sources and run rules

- Current main: `ffe5292b3164a3eb7e2b5d18eaadcbafdcd2b385`
- #8528 semantics: `research/decision_regret_8528_t0_a01_20261008/PROTOCOL.md` at commit `3f6bc41adaaf6dcc96ff0fd0deea5c691140c8d8`; raw/audit hashes are recorded in this package manifest.
- Candidate, independent auditor, inputs, tests, this protocol, and environment description are source-frozen before formal execution.
- Exactly one candidate command followed by one independent audit command; no retries. Preserve exact stdout, raw JSON, audit JSON, command/environment receipt, and hashes.
- No model, GUI, participant, external service, runtime action, Docker/WSL, or live allocation. This finite CPU computation does not benefit from a container boundary.

## Exact fixture values and denominators

Within each stratum, the 12 assigned opportunity regrets by route are: S1/A `[3,3,2,2,1,1,0,0,0,0,0,0]`; S2/A all zero; S1/B twelve ones; S2/B all zero; C all zero in both strata. Each opportunity value is independently derived as the sum of four binary per-open-tick regret values reconstructed from selected action and audit-only target state. Thus pooled means A/B are both 12/24 = 0.5; pooled ES20 is A `(3+3+2+2+1)/5 = 2.2`, B `1`; macro means are both 0.5; macro ES20 is A `(8/3+0)/2 = 4/3`, B `(1+0)/2 = 0.5`. These are authored finite contrasts, not sampled route outcomes.
