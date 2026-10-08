# Preregistration — Issue #5917 T1-01

Allocation: `VERIFIER-SELECTION-5917-T1-LOCALCPU-20261001-01`
Base main: `4b7fe7837e4ee8c0d035ebfbf52baf014f042295`
Branch: `research/selection-aware-verifier-5917-t1-20261001`
Path: `research/analysis/selection_aware_verifier_5917_t1_v1/`
Owner: this Codex task; host-local CPU only. No shared GPU/Docker slot, model, GUI, task effect, or network is used by the candidate/audit processes.

## H / T / D / C / U

**H.** With difficulty-dependent routing and positive support, selected-only accuracy is biased; exact-known-propensity HT and DR with either correctly specified nuisance component recover the finite-population mean in expectation. Both-wrong DR remains biased. A verifier with a zero-support stratum is non-identifiable and must be refused.

**T.** Fixture is `fixture.json`: 8 rows (2 families × 2 difficulty strata × 2 replicates), two eligible side-effect-free verifiers A/B, deterministic opposite outcomes (A=1/B=0 on easy; A=0/B=1 on hard), true accuracy .5 each, cost A=1/B=2, independent per-row routing with p(A|easy)=.9, p(A|hard)=.1 and p(B)=1-p(A). Enumerate all 256 assignments with exact probabilities. Estimators: selected-only conditional mean (undefined draws remain explicit), HT mean, DR with true p/wrong q=.25, DR with wrong p=.5/true q, and DR with both wrong (p=.5,q=.25). No clipping. Report draw-weighted bias, variance, MSE, 2.5/50/97.5% randomization quantiles, undefined mass, Kish ESS, max inverse-propensity weight, and family×difficulty calibration. Include every assignment/estimator row in candidate raw output so per-draw losses are retained.

**Zero-support control.** In a separate policy set p(B)=0 and p(A)=1 on all hard rows, preserving easy propensities. Enumerate every feasible logging assignment under two worlds differing only in B's unobserved hard outcomes (all 1 vs all 0). Require identical observed logs while B's census accuracy changes .5→0; disposition is `NONIDENTIFIABLE_FROM_LOGS`, with no point estimate.

**D.** `METHOD_PASS_SCOPED` iff all 256 probabilities sum to 1 within 1e-12; selected-only conditional bias magnitude ≥.35 for A and B; HT and true-p/wrong-q DR have absolute expected bias <1e-12 and MSE below selected-only for both; either-correct-component DR expected bias <1e-12; both-wrong DR bias magnitude ≥.35; calibration error <1e-12; maximum weight=10; zero-support refusal/log-world equivalence hold; independent auditor matches every raw draw and rejects exactly the three frozen mutations (draw probability, omitted draw, false zero-support estimate). Otherwise retain FAIL/HOLD without changes or rerun.

**C/U.** Synthetic, deterministic, eight-row population with known propensities and deliberately strong routing/outcome dependence. This is method/arithmetic evidence only, not real verifier competence, a live logging policy, T2 shadow safety, task correctness, or a production routing rule.

**Execution record.** Preregistered on #5917 before candidate. Docker Desktop CLI remains unresponsive and C: has <100 MiB free; this side-effect-free fixture needs no packages, so the candidate and independent auditor will run once each as separate local Windows Python 3.11.9 processes with in-memory pipes. Container substitution was not attempted; the host-CPU deviation will be retained. No GPU/model/provider/GUI/network/file-system writes. Audit runs only if candidate exits 0.
