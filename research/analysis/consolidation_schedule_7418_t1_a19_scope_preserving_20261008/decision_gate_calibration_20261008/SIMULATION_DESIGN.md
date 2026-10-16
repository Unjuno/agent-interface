# A19 decision-gate calibration (pre-run design)

This is a separate, model-free analysis of the A19 decision rule. It does not consume the A19 formal allocation or change its frozen thresholds.

## H / T / D / C / U

**H — hypothesis.** The A19 rule's requirement for one same-direction schedule pair with an absolute accuracy gap of at least 0.10 in each of three seeds may have different false-sensitivity and detection rates when its 60 answers per seed/arm are independent versus strongly clustered by the six repeated prefixes.

**T — test.** Simulate the exact implemented gate for four arms in auditor order (`episodic_only`, `per_episode`, `batch_2`, `terminal`), three independent seeds, and 60 scored answers per seed/arm. For each simulated allocation, evaluate all six arm pairs and require the same pair to exceed the threshold in the same direction in every seed. Compare two null structures: (1) independent Bernoulli answers within each arm/seed; and (2) six independent prefix clusters with all ten answers within a prefix perfectly correlated. Evaluate null accuracy 0.50 for all arms, then one arm at 0.60 or 0.70 versus three arms at 0.50. Run 200,000 simulated allocations per scenario with Python `random.Random` seed 84062026. Use inverse-CDF Binomial draws; for each seed/arm, use the same uniform variate to couple the independent-item and prefix-cluster scenarios. Distinct arms and seeds remain independent within each scenario.

**D — decision.** Report estimated false-sensitivity probability under the equal-accuracy null and detection probability at +0.10 and +0.20. Flag the gate as needing qualification before formal freeze if the independent-answer null estimate exceeds 5%, or if the +0.10 detection estimate is below 50%. Do not change A19 thresholds in this analysis. A result below both flags only supports the gate under these simulated assumptions.

**C — competing explanations.** Real model answers are neither independent Bernoulli trials nor perfectly correlated prefix blocks. Same-seed generations across schedules may also be correlated. The model is a diagnostic stress bracket, not an empirical model of Qwen3 or a formal p-value.

**U — limits.** The 200,000-replicate Monte Carlo has finite sampling error. Only three accuracy settings are tested. The calibration does not establish actual cadence accuracy, model variance, query-family behavior, or GUI effects, and does not replace the A19 run or independent raw audit.

## Reproduction

From this directory, run:

```sh
PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 simulate_decision_gate_null.py --output SIMULATION_RESULT.json
```

The script uses only the Python standard library. The exact source hash, Python version, command, and result are recorded in `SIMULATION_RESULT.json`.
