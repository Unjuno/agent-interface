"""Deterministic fixture generator. Oracle rows are serialized separately."""
import random


def generate(seed=7993002, cohorts=32, n=40, pi=(0.25, 0.75), risk=(0.40, 0.10)):
    rng = random.Random(seed)
    candidate_rows = []
    oracle_rows = []
    for c in range(cohorts):
        for i in range(n):
            x = i % 2
            y = int(rng.random() < risk[x])
            observed = int(rng.random() < pi[x])
            key = {"cohort": c, "row": i}
            candidate_rows.append({**key, "x": x, "pi": pi[x], "observed": observed,
                                   "label": y if observed else None})
            oracle_rows.append({**key, "x": x, "pi": pi[x], "y": y, "observed": observed})
    candidate = {"contract": {"known_propensities": True, "conditional_independence": True,
                               "population_risk": 0.25, "strata": [0, 1]},
                 "cohorts": cohorts, "n_per_cohort": n, "rows": candidate_rows}
    oracle = {"rows": oracle_rows}
    return candidate, oracle
