# Independent lower-bound audit

`audit_pairwise_lower_bound.py` uses exact Binomial probability mass functions rather than the calibration runner's inverse-CDF Monte Carlo sampler. For one predesignated pair under an equal-accuracy null, it computes the probability that the same direction exceeds the threshold in all three seeds. That event is a subset of the six-pair familywise event, so the simulated union rate must be at least this large, up to Monte Carlo error.

Command:

```sh
PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 audit_pairwise_lower_bound.py
```

Exit code 0; status `PASS_SINGLE_PAIR_LOWER_BOUND_SANITY_CHECK`. Exact single-pair probabilities were 0.7837% for independent 60-item answers (Monte Carlo six-pair rate 4.1615%) and 11.6107% for six perfect prefix clusters (six-pair rate 43.6795%). The checker verified both inequalities and bound its input to `SIMULATION_RESULT.json` SHA-256 `32e78a6b53388ca61ab7d878e5d1e7242e282eb7b269eb243ed23f29613c3b10`.

This is a limited sanity check, not an independent reproduction of the six-pair union probability or a model of actual answer dependence.

## Exact equal-accuracy null-union cross-check

`audit_null_familywise_exact.py` separately enumerates the four independent Binomial arm counts for one seed, maps each count tuple to its directed pair-contrast mask, then intersects those masks across three independent seeds. It does not use the simulation runner's random sampler. Command:

```sh
PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 audit_null_familywise_exact.py
```

Exit code 0; status `PASS_EXACT_NULL_UNION_CROSSCHECK`. Exact familywise rates were 4.1555% for independent 60-item answers and 43.5984% for six perfect prefix clusters. The Monte Carlo rates (4.1615% and 43.6795%) differed by 0.13 and 0.73 Monte Carlo standard errors. Source SHA-256: `04ca4f0f9c68d5a3784e22288f93cb14612c06da32e17b81d6435ecfcb856e3c`; output SHA-256: `86f7f10cbbe56a886496473a7235c361b7eb20891ac6f2770b4bf8c0a37117ee`.

This exactly verifies the equal-accuracy null union rates only. The separate `audit_nonnull_power_exact.py` enumerates the four non-null alternatives and cross-checks all four Monte Carlo power estimates; see `EXACT_POWER_AUDIT.md` and `NONNULL_POWER_EXACT_AUDIT.json`. Neither audit measures actual model dependence.
