#!/usr/bin/env python3
"""Exploratory repeated-cohort IPCW check; deterministic, standard library only."""
import json
import random
import statistics


def one_cohort(rng, n=400, pi_low=0.25, pi_high=0.75):
    # X is balanced; outcome risk varies by X. Follow-up is independent of Y given X.
    # Candidate sees X and known design propensity, never hidden Y when R=0.
    rows = []
    for i in range(n):
        x = i % 2
        px = 0.40 if x == 0 else 0.10
        y = int(rng.random() < px)
        pi = pi_low if x == 0 else pi_high
        observed = int(rng.random() < pi)
        rows.append({"x": x, "pi": pi, "observed": observed,
                     "y": y if observed else None, "oracle_y": y})
    complete = [r["y"] for r in rows if r["observed"]]
    cc = sum(complete) / len(complete)
    ht = sum((r["y"] / r["pi"]) for r in rows if r["observed"]) / n
    # HT targets finite-cohort realized risk over the independent follow-up
    # mask conditional on this cohort; it is not a risk certificate.
    truth = sum(r["oracle_y"] for r in rows) / n
    return {"truth": truth, "cc": cc, "ht": ht, "n_observed": len(complete)}


def main():
    seed, cohorts, n = 7993001, 20000, 400
    rng = random.Random(seed)
    runs = [one_cohort(rng, n=n) for _ in range(cohorts)]
    true_population_risk = 0.25
    cc = [r["cc"] for r in runs]
    ht = [r["ht"] for r in runs]
    truth = [r["truth"] for r in runs]
    positivity_case = {"pi_low": 0.0, "pi_high": 0.75,
                       "disposition": "UNKNOWN", "reason": "zero support in X=0"}
    observed_row = {"x": 0, "observed": 1, "y": 0, "pi": 0.5}
    hidden_world_a = {**observed_row, "oracle_y": 0}
    hidden_world_b = {**observed_row, "oracle_y": 1}
    out = {
        "protocol": "issue-7993-superpopulation-ipcw-a01-exploratory",
        "environment": "host Python; no container; exploratory only",
        "seed": seed, "cohorts": cohorts, "cohort_n": n,
        "population_risk": true_population_risk,
        "outcome_by_stratum": {"x0": 0.40, "x1": 0.10},
        "followup": "independent Bernoulli conditional on balanced X; pi=(0.25,0.75), known",
        "complete_case_mean": statistics.fmean(cc),
        "ht_mean": statistics.fmean(ht),
        "truth_mean": statistics.fmean(truth),
        "ht_bias_vs_population": statistics.fmean(ht) - true_population_risk,
        "ht_bias_vs_realized_cohort_mean": statistics.fmean([r["ht"]-r["truth"] for r in runs]),
        "cc_bias_vs_population": statistics.fmean(cc) - true_population_risk,
        "ht_population_sd": statistics.pstdev(ht),
        "cc_population_sd": statistics.pstdev(cc),
        "mean_observed": statistics.fmean([r["n_observed"] for r in runs]),
        "positivity_case": positivity_case,
        "observational_equivalence": {
            "candidate_visible_equal": hidden_world_a["x"] == hidden_world_b["x"] and hidden_world_a["observed"] == hidden_world_b["observed"] and hidden_world_a["y"] == hidden_world_b["y"] and hidden_world_a["pi"] == hidden_world_b["pi"],
            "world_a_true_risk": 0, "world_b_true_risk": 1,
            "candidate_disposition": "UNKNOWN without a justified observation model"
        }
    }
    print(json.dumps(out, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
