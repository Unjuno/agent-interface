#!/usr/local/bin/python3
"""Deterministic, synthetic T0 candidate for Issue #7889; standard library only."""
import csv
import hashlib
import json
import math
import os
import statistics

ROOT = "/src"
OUT = "/out"
INPUT = json.load(open(os.path.join(ROOT, "study-input.json"), encoding="utf-8"))
NORMAL = statistics.NormalDist()


def normal(seed, *coords):
    key = "|".join([seed, *(str(x) for x in coords)]).encode()
    n = int.from_bytes(hashlib.sha256(key).digest()[:8], "big")
    u = (n + 0.5) / 2**64
    return NORMAL.inv_cdf(u)


def exact_phi(x):
    return NORMAL.cdf(x)


def truth(profile, design):
    var = profile["app_var"] / design["apps"]
    var += profile["task_var"] / (design["apps"] * design["tasks_per_app"])
    var += profile["error_var"] / (design["apps"] * design["tasks_per_app"] * design["repeats"])
    return var, exact_phi((INPUT["beta"] - INPUT["practical_margin"]) / math.sqrt(var))


def estimate(values, A, T, S):
    app_means, task_means = [], []
    ss_error = 0.0
    for app in values:
        per_task = [sum(task) / S for task in app]
        app_mean = sum(per_task) / T
        app_means.append(app_mean)
        task_means.append(per_task)
        for task, tm in zip(app, per_task):
            ss_error += sum((v - tm) ** 2 for v in task)
    ms_error = ss_error / (A * T * (S - 1))
    ss_task = sum((tm - am) ** 2 for tms, am in zip(task_means, app_means) for tm in tms)
    ms_task = S * ss_task / (A * (T - 1))
    grand = sum(app_means) / A
    ms_app = T * S * sum((am - grand) ** 2 for am in app_means) / (A - 1)
    return ms_app, ms_task, ms_error, (ms_app - ms_task) / (T * S), (ms_task - ms_error) / S, ms_error, grand


def exact_binomial_prob(n, p, ordinary, hard, margin):
    total = 0.0
    for k in range(n + 1):
        mean = ((n - k) * ordinary + k * hard) / n
        if mean > margin:
            total += math.comb(n, k) * (p**k) * ((1 - p) ** (n - k))
    return total


def paired_cell_gate(cells):
    if any(any(v is None for v in outcomes) for outcomes in cells.values()):
        return "HOLD_UNKNOWN_OUTCOME"
    if any(len(outcomes) != 2 for outcomes in cells.values()):
        return "HOLD_INCOMPLETE_PAIRED_CELLS"
    return "PASS_COMPLETE_PAIRED_CELLS"


def main():
    rows = []
    rare_rows = []
    summary = {"study_id": INPUT["study_id"], "profiles": {}, "rare_hard": {}, "malformed_controls": {}}
    for profile in INPUT["profiles"]:
        summary["profiles"][profile["id"]] = {}
        for design in INPUT["designs"]:
            A, T, S = design["apps"], design["tasks_per_app"], design["repeats"]
            var_true, p_true = truth(profile, design)
            for r in range(INPUT["replicates"]):
                values = []
                for a in range(A):
                    app_route = math.sqrt(profile["app_var"]) * normal(INPUT["seed"], profile["id"], design["id"], r, "app", a)
                    app = []
                    for t in range(T):
                        task_route = math.sqrt(profile["task_var"]) * normal(INPUT["seed"], profile["id"], design["id"], r, "task", a, t)
                        task = []
                        for s in range(S):
                            err = math.sqrt(profile["error_var"]) * normal(INPUT["seed"], profile["id"], design["id"], r, "error", a, t, s)
                            task.append(INPUT["beta"] + app_route + task_route + err)
                        app.append(task)
                    values.append(app)
                m_app, m_task, m_err, e_app, e_task, e_err, grand = estimate(values, A, T, S)
                rows.append(["normal", profile["id"], design["id"], r, m_app, m_task, m_err, e_app, e_task, e_err, grand, int(grand > INPUT["practical_margin"])])
            block = [row for row in rows if row[1] == profile["id"] and row[2] == design["id"]]
            rec = {"design": design, "true_mean_variance": var_true, "exact_decision_probability": p_true}
            for idx, name in [(4, "ms_app"), (5, "ms_task"), (6, "ms_error"), (7, "app_var_est"), (8, "task_var_est"), (9, "error_var_est")]:
                rec["mean_" + name] = sum(float(row[idx]) for row in block) / len(block)
            rec["empirical_decision_probability"] = sum(int(row[11]) for row in block) / len(block)
            summary["profiles"][profile["id"]][design["id"]] = rec

    rare = INPUT["rare_hard"]
    summary["rare_hard"] = {}
    for design in INPUT["designs"]:
        n = design["apps"] * design["tasks_per_app"]
        p_exact = exact_binomial_prob(n, rare["hard_probability"], rare["ordinary_contrast"], rare["hard_contrast"], rare["margin"])
        hit = 0
        for r in range(INPUT["replicates"]):
            k = sum(normal(INPUT["seed"], "rare_hard", design["id"], r, i) < NORMAL.inv_cdf(rare["hard_probability"]) for i in range(n))
            mean = ((n-k)*rare["ordinary_contrast"] + k*rare["hard_contrast"]) / n
            hit += mean > rare["margin"]
            rare_rows.append([design["id"], r, n, k, mean, int(mean > rare["margin"])])
        summary["rare_hard"][design["id"]] = {"distinct_tasks": n, "exact_decision_probability": p_exact, "empirical_decision_probability": hit / INPUT["replicates"]}

    # Fail-closed structural gate: never estimate after a missing/unknown paired cell.
    summary["malformed_controls"] = {
        "one_missing_paired_outcome": paired_cell_gate({"task-1": [0.0]}),
        "one_unknown_outcome": paired_cell_gate({"task-1": [0.0, None]}),
        "complete_control": paired_cell_gate({"task-1": [0.0, 1.0]})
    }
    with open(os.path.join(OUT, "raw-ledger.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["kind", "profile", "design", "replicate", "ms_app", "ms_task", "ms_error", "app_var_est", "task_var_est", "error_var_est", "grand_mean", "decision_pass"])
        w.writerows(rows)
    with open(os.path.join(OUT, "rare-ledger.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["design", "replicate", "distinct_tasks", "hard_tasks", "sample_mean", "decision_pass"])
        w.writerows(rare_rows)
    with open(os.path.join(OUT, "candidate-result.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, sort_keys=True, indent=2)
        f.write("\n")


if __name__ == "__main__":
    main()
