#!/usr/local/bin/python3
"""Independent raw-ledger auditor; does not import or execute candidate.py."""
import csv
import hashlib
import json
import math
import os
import statistics
import sys

ROOT = "/src"
OUT = "/out"
I = json.load(open(os.path.join(ROOT, "study-input.json"), encoding="utf-8"))
N = statistics.NormalDist()


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def close(x, y, t):
    return math.isfinite(float(x)) and abs(float(x) - float(y)) <= t


def exact(profile, design):
    v = profile["app_var"] / design["apps"]
    v += profile["task_var"] / (design["apps"] * design["tasks_per_app"])
    v += profile["error_var"] / (design["apps"] * design["tasks_per_app"] * design["repeats"])
    return v, N.cdf((I["beta"] - I["practical_margin"]) / math.sqrt(v))


def main():
    raw_path = os.path.join(OUT, "raw-ledger.csv")
    rare_path = os.path.join(OUT, "rare-ledger.csv")
    result_path = os.path.join(OUT, "candidate-result.json")
    rows = list(csv.DictReader(open(raw_path, newline="", encoding="utf-8")))
    rare_rows = list(csv.DictReader(open(rare_path, newline="", encoding="utf-8")))
    result = json.load(open(result_path, encoding="utf-8"))
    checks = []
    def check(name, ok, evidence=None):
        checks.append({"check": name, "pass": bool(ok), "evidence": evidence})

    expected_rows = len(I["profiles"]) * len(I["designs"]) * I["replicates"]
    check("ledger_row_count", len(rows) == expected_rows, {"expected": expected_rows, "actual": len(rows)})
    check("all_finite_rows", all(all(math.isfinite(float(r[k])) for k in ("ms_app", "ms_task", "ms_error", "app_var_est", "task_var_est", "error_var_est", "grand_mean")) for r in rows))
    keys = [(r["profile"], r["design"], int(r["replicate"])) for r in rows]
    check("unique_complete_replication_keys", len(keys) == len(set(keys)) and len(set(keys)) == expected_rows)
    gates = {"component_mean_abs_error_max": 0.0, "decision_frequency_abs_error_max": 0.0, "main_only_breadth_advantage": None, "interaction_breadth_advantages": {}}
    for p in I["profiles"]:
        for d in I["designs"]:
            block = [r for r in rows if r["kind"] == "normal" and r["profile"] == p["id"] and r["design"] == d["id"]]
            v, prob = exact(p, d)
            k = lambda field: sum(float(r[field]) for r in block) / len(block)
            comp_errors = [abs(k("app_var_est") - p["app_var"]), abs(k("task_var_est") - p["task_var"]), abs(k("error_var_est") - p["error_var"])]
            gates["component_mean_abs_error_max"] = max(gates["component_mean_abs_error_max"], *comp_errors)
            freq = sum(int(r["decision_pass"]) for r in block) / len(block)
            gates["decision_frequency_abs_error_max"] = max(gates["decision_frequency_abs_error_max"], abs(freq-prob))
            claimed = result["profiles"][p["id"]][d["id"]]
            check("summary_matches_raw_" + p["id"] + "_" + d["id"], close(claimed["empirical_decision_probability"], freq, 1e-12) and close(claimed["exact_decision_probability"], prob, 1e-12) and close(claimed["true_mean_variance"], v, 1e-12))

    main = result["profiles"]["main_only"]
    broad_main = max(main["within_app_breadth"]["empirical_decision_probability"], main["app_breadth"]["empirical_decision_probability"])
    gates["main_only_breadth_advantage"] = broad_main - main["repeat_cells"]["empirical_decision_probability"]
    for pid in ("task_interaction", "app_interaction", "combined_interactions"):
        prof = result["profiles"][pid]
        broad = max(prof["within_app_breadth"]["empirical_decision_probability"], prof["app_breadth"]["empirical_decision_probability"])
        gates["interaction_breadth_advantages"][pid] = broad-prof["repeat_cells"]["empirical_decision_probability"]
    check("component_gate", gates["component_mean_abs_error_max"] <= I["thresholds"]["component_mean_abs_error_max"], gates["component_mean_abs_error_max"])
    check("decision_frequency_gate", gates["decision_frequency_abs_error_max"] <= I["thresholds"]["decision_frequency_abs_error_max"], gates["decision_frequency_abs_error_max"])
    check("main_only_gate", gates["main_only_breadth_advantage"] <= I["thresholds"]["main_only_breadth_advantage_max"], gates["main_only_breadth_advantage"])
    check("interaction_gate", all(x >= I["thresholds"]["interaction_breadth_advantage_min"] for x in gates["interaction_breadth_advantages"].values()), gates["interaction_breadth_advantages"])

    # Independently recalculate rare-task exact and empirical probabilities from its raw rows.
    rare = I["rare_hard"]
    rare_checks = {}
    for d in I["designs"]:
        n = d["apps"] * d["tasks_per_app"]
        exactp = sum(math.comb(n, k)*rare["hard_probability"]**k*(1-rare["hard_probability"])**(n-k)
                     for k in range(n+1)
                     if ((n-k)*rare["ordinary_contrast"]+k*rare["hard_contrast"])/n > rare["margin"])
        item = result["rare_hard"][d["id"]]
        rb = [r for r in rare_rows if r["design"] == d["id"]]
        empirical = sum(int(r["decision_pass"]) for r in rb) / len(rb)
        check("rare_ledger_rows_" + d["id"], len(rb) == I["replicates"] and all(int(r["distinct_tasks"]) == n for r in rb))
        check("rare_ledger_binomial_" + d["id"], all(0 <= int(r["hard_tasks"]) <= n and close(float(r["sample_mean"]), ((n-int(r["hard_tasks"]))*rare["ordinary_contrast"]+int(r["hard_tasks"])*rare["hard_contrast"])/n, 1e-12) for r in rb))
        check("rare_ledger_decisions_" + d["id"], close(item["empirical_decision_probability"], empirical, 1e-12) and abs(empirical-exactp) <= I["thresholds"]["decision_frequency_abs_error_max"])
        rare_checks[d["id"]] = {"exact": exactp, "reported": item["exact_decision_probability"], "distinct_tasks": n, "empirical": empirical}
        check("rare_hard_exact_" + d["id"], close(item["exact_decision_probability"], exactp, 1e-12) and item["distinct_tasks"] == n)
    check("rare_hard_repeat_lowest", result["rare_hard"]["repeat_cells"]["exact_decision_probability"] < min(result["rare_hard"]["within_app_breadth"]["exact_decision_probability"], result["rare_hard"]["app_breadth"]["exact_decision_probability"]))
    check("missing_cell_holds", result["malformed_controls"]["one_missing_paired_outcome"] == "HOLD_INCOMPLETE_PAIRED_CELLS")
    check("unknown_outcome_holds", result["malformed_controls"]["one_unknown_outcome"] == "HOLD_UNKNOWN_OUTCOME")
    check("complete_cell_control_passes", result["malformed_controls"]["complete_control"] == "PASS_COMPLETE_PAIRED_CELLS")

    # Mutation escapes are probed against the independent gates and expected invariants.
    mutation_tol = I["thresholds"]["decision_frequency_abs_error_max"]
    drep = next(d for d in I["designs"] if d["id"] == "repeat_cells")
    p_task = next(p for p in I["profiles"] if p["id"] == "task_interaction")
    p_app = next(p for p in I["profiles"] if p["id"] == "app_interaction")
    actual_task = exact(p_task, drep)[1]
    task_omitted_var = p_task["error_var"] / (drep["apps"]*drep["tasks_per_app"]*drep["repeats"])
    task_omitted_prob = N.cdf((I["beta"]-I["practical_margin"])/math.sqrt(task_omitted_var))
    actual_app = exact(p_app, drep)[1]
    app_omitted_var = p_app["error_var"] / (drep["apps"]*drep["tasks_per_app"]*drep["repeats"])
    app_omitted_prob = N.cdf((I["beta"]-I["practical_margin"])/math.sqrt(app_omitted_var))
    combined = next(p for p in I["profiles"] if p["id"] == "combined_interactions")
    actual_combined = exact(combined, drep)[1]
    falsely_iid_var = (combined["app_var"]+combined["task_var"]+combined["error_var"]) / (drep["apps"]*drep["tasks_per_app"]*drep["repeats"])
    falsely_iid_prob = N.cdf((I["beta"]-I["practical_margin"])/math.sqrt(falsely_iid_var))
    mutations = {
        "repeats_as_independent_tasks": abs(falsely_iid_prob-actual_combined) > mutation_tol,
        "omit_task_interaction": abs(task_omitted_prob-actual_task) > mutation_tol,
        "pool_away_app_effect": abs(app_omitted_prob-actual_app) > mutation_tol,
        "drop_unknown_outcomes": result["malformed_controls"]["one_unknown_outcome"] == "HOLD_UNKNOWN_OUTCOME",
        "omit_rare_hard_stratum": max(abs(1.0-rare_checks[d["id"]]["exact"]) for d in I["designs"]) > mutation_tol
    }
    for m, detected in mutations.items():
        check("mutation_detected_" + m, detected)
    gate_pass = all(c["pass"] for c in checks)
    audit = {"status": "PASS_METHOD_SCOPED" if gate_pass else "FAIL_METHOD", "checks": checks,
             "gate_metrics": gates, "rare_hard_exact": rare_checks,
             "sha256": {"study_input": sha(os.path.join(ROOT,"study-input.json")), "candidate_source": sha(os.path.join(ROOT,"candidate.py")), "auditor_source": sha(os.path.join(ROOT,"auditor.py")), "raw_ledger": sha(raw_path), "rare_ledger": sha(rare_path), "candidate_result": sha(result_path)}}
    with open(os.path.join(OUT, "audit-result.json"), "w", encoding="utf-8") as f:
        json.dump(audit, f, sort_keys=True, indent=2)
        f.write("\n")
    print(json.dumps({"status": audit["status"], "checks": len(checks), "failed": [c["check"] for c in checks if not c["pass"]], "sha256": audit["sha256"]}, sort_keys=True))
    return 0 if gate_pass else 2


if __name__ == "__main__":
    sys.exit(main())
