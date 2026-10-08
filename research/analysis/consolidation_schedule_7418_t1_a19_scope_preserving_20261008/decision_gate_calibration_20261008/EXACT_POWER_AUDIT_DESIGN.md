# Exact non-null decision-gate audit (pre-run design)

This supplementary exact enumeration checks the two non-null power scenarios from the A19 decision-gate Monte Carlo. It is separate from the formal A19 allocation and does not change its thresholds.

## H / T / D / C / U

**H — hypothesis.** Exact finite-state enumeration of the A19 decision rule will agree with the Monte Carlo sensitivity rates for +0.10 and +0.20 arm-accuracy scenarios within five Monte Carlo standard errors.

**T — test.** Enumerate every four-arm Binomial count tuple for one seed under each scenario, convert it to the six directed pairwise threshold indicators, and exactly propagate their intersection over three independent seeds. For independent answers use 60 Bernoulli items per seed/arm and threshold 6; for perfect-prefix clustering use six Bernoulli prefix blocks per seed/arm, each representing ten perfectly correlated answers, and threshold one block. Compare exact probabilities with the registered Monte Carlo rates for `episodic_only` at 0.60 or 0.70 and the other arms at 0.50.

**D — decision.** `PASS_EXACT_POWER_CROSSCHECK` if all four exact probabilities are within five Monte Carlo standard errors of the corresponding simulation estimates; otherwise `FAIL_CROSSCHECK`. Preserve the existing labels and numerical threshold regardless of outcome.

**C — competing explanations.** The two dependence structures are idealizations; real model answers may have more complicated cross-prefix and cross-arm dependence. Agreement validates only this finite probability calculation and Monte Carlo implementation.

**U — limits.** No Qwen3, corpus, query, or GUI behavior is sampled. Exactness is conditional on independent arm/seed Binomial draws with the listed probabilities.

## Reproduction

```sh
PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 audit_nonnull_power_exact.py
```

The source and design hashes, exact output, Monte Carlo comparison, and scope are stored in `NONNULL_POWER_EXACT_AUDIT.json`.
