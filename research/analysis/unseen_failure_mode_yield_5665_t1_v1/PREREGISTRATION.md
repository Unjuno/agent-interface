# Issue #5665 T1 — unseen failure-mode discovery method construction

Allocation: issue5665-failure-mode-yield-t1-20261001-01  
Base main: 5ff239141f49c1603c0f6b078268f4a2f6e082df  
Branch: research/issue5665-failure-mode-yield-t1-20261001-01  
Additive path: research/analysis/unseen_failure_mode_yield_5665_t1_v1/

## H / T / D / C / U

- **H:** In a fixed synthetic IID categorical failure-mode generator, singleton mass f1/n predicts unseen-class encounter better than the frozen trailing-K=20 novelty-rate baseline, both against the exact unobserved probability mass and a separately sampled held-out validation batch. This is method construction only; it cannot establish empirical repository coverage.
- **T:** Generate 200 independent replicates. Each has 100 conditional-on-failure training draws and 500 held-out draws from labels F0–F7 with integer weights [500,250,120,60,30,20,10,10]. Candidate is Good–Turing f1/n. Baseline is the fraction of distinct first-seen labels in the final 20 training draws. Save complete train/validation labels, unit IDs, taxonomy and stratum IDs. Add four controls: fivefold within-cluster duplicate traces, taxonomy-version split, explicit validation-distribution shift with a new label, and one missing training outcome. The independent raw-only auditor recomputes predictions and scores and tests four corresponding rejection/hold mutations.
- **D:** METHOD_PASS if all 200 IID rows are eligible, all four held controls have the preregistered disposition, the raw-only audit returns zero errors, and all four mutation controls are detected. Separately report whether mean absolute prediction error for f1/n is below the trailing-K baseline against both exact missing mass and finite held-out rate. A comparison failure is recorded as METHOD_COMPARISON_FAIL; it does not invalidate a successful integrity audit. No H_PASS_SCOPED claim is made from this T1.
- **C:** A recency baseline can be stronger under clustered discovery; an apparent low new-mode yield may reflect taxonomy coarsening or a changed distribution rather than saturation. The synthetic IID advantage, if observed, is conditional on this known generator.
- **U:** Synthetic labels, one frozen taxonomy, known probabilities, and independent draws omit adaptive search, adjudicator disagreement, censored real outcomes, correlated real episodes, changing agent versions, and high-impact rare failures. This estimates conditional-on-failure class mass only, not per-trial failure probability, safety risk, or population-wide fault coverage.

## Frozen execution

Source SHA-256: runner 8ecfa3b3fd6009de70c5ba3854b8cf9f8c927d8a719f73cf9150c3e9d932d3c2; auditor cefb6efa1b7c67f6a6eca46e732da9e9e564de9fbd698acccd5a407949a3ae6dd.

Exact candidate command, once only:
python run.py --out results/t1-host-01/raw.jsonl

If and only if runner exit code is 0, run the independent auditor exactly once:
python audit.py results/t1-host-01/raw.jsonl

Environment: CPython 3.11.9, Windows 10 host CPU. Docker/OrbStack has no allocation for this study; no GPU, model, network, GUI, real task input, or external effect is permitted. Output path must be new and empty. Preserve stdout, stderr, exit status, raw JSONL and the auditor's exact output. No tuning, retry, generator substitution, or result-based taxonomy edits.
