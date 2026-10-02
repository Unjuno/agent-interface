import copy
import hashlib
import json
import sys
from pathlib import Path


EXPECTED = {
    "selection_reversal": {
        "A": {"n": 4, "successes": 2, "success_rate": 0.5, "mean_time": 5.5},
        "B": {"n": 4, "successes": 4, "success_rate": 1.0, "mean_time": 5.0},
        "local": {"n": 2, "successes": 2, "success_rate": 1.0, "mean_time": 1.0},
        "assignment_delta": (-0.5, 0.5), "selected_delta": (0.0, -4.0),
    },
    "exposure_independent_null": {
        "A": {"n": 4, "successes": 4, "success_rate": 1.0, "mean_time": 4.0},
        "B": {"n": 4, "successes": 4, "success_rate": 1.0, "mean_time": 5.0},
        "local": {"n": 2, "successes": 2, "success_rate": 1.0, "mean_time": 4.0},
        "assignment_delta": (0.0, -1.0), "selected_delta": (0.0, -1.0),
    },
}
ORACLE_TASKS = {
    "selection_reversal": [
        ("E1", "easy", "local", 1, 1, 1, 5),
        ("E2", "easy", "local", 1, 1, 1, 5),
        ("H1", "hard", "fallback", 0, 10, 1, 5),
        ("H2", "hard", "fallback", 0, 10, 1, 5),
    ],
    "exposure_independent_null": [
        ("E1", "easy", "local", 1, 4, 1, 5),
        ("E2", "easy", "fallback", 1, 4, 1, 5),
        ("H1", "hard", "local", 1, 4, 1, 5),
        ("H2", "hard", "fallback", 1, 4, 1, 5),
    ],
}


def summarize(rows):
    n = len(rows)
    return {"n": n, "successes": sum(r["success"] for r in rows),
            "success_rate": sum(r["success"] for r in rows) / n if n else None,
            "mean_time": sum(r["total_time"] for r in rows) / n if n else None}


def audit(doc):
    errors = []
    if doc.get("estimand_label") != "SYNTHETIC_AS_ASSIGNED_DESCRIPTIVE_NOT_CAUSAL":
        errors.append("causal_overclaim_label")
    if doc.get("exposure_label") != "POST_ASSIGNMENT_SELECTED_SUBSET_DESCRIPTIVE_ONLY":
        errors.append("exposure_not_labeled_post_assignment")
    if len(doc.get("rows", [])) != 16:
        errors.append("assignment_denominator_row_count")
    oracle_rows = []
    for scenario, tasks in ORACLE_TASKS.items():
        for task, difficulty, path, a_success, a_time, b_success, b_time in tasks:
            oracle_rows.append({"scenario": scenario, "task": task, "difficulty": difficulty,
                                "assigned_arm": "A", "actual_path": path,
                                "admission": path == "local", "admission_timing": "POST_ASSIGNMENT",
                                "success": a_success, "total_time": a_time,
                                "fallback_time": a_time if path == "fallback" else 0})
            oracle_rows.append({"scenario": scenario, "task": task, "difficulty": difficulty,
                                "assigned_arm": "B", "actual_path": "plain", "admission": True,
                                "admission_timing": "POST_ASSIGNMENT", "success": b_success,
                                "total_time": b_time, "fallback_time": 0})
    if doc.get("rows") != oracle_rows:
        errors.append("rows_do_not_match_independent_potential_outcome_oracle")
    computed = {}
    for scenario, expected in EXPECTED.items():
        rows = [r for r in oracle_rows if r.get("scenario") == scenario]
        if len(rows) != 8:
            errors.append("scenario_denominator:" + scenario)
        if any(r.get("admission_timing") != "POST_ASSIGNMENT" for r in rows):
            errors.append("pretreatment_relabel:" + scenario)
        a = summarize([r for r in rows if r["assigned_arm"] == "A"])
        b = summarize([r for r in rows if r["assigned_arm"] == "B"])
        local = summarize([r for r in rows if r["assigned_arm"] == "A" and r["actual_path"] == "local"])
        if a != expected["A"] or b != expected["B"] or local != expected["local"]:
            errors.append("recomputed_summary_mismatch:" + scenario)
        if any(r["assigned_arm"] == "A" and r["actual_path"] == "fallback" and r["fallback_time"] != r["total_time"] for r in rows):
            errors.append("fallback_time_dropped:" + scenario)
        assigned_delta = (a["success_rate"] - b["success_rate"], a["mean_time"] - b["mean_time"])
        selected_delta = (local["success_rate"] - b["success_rate"], local["mean_time"] - b["mean_time"])
        if assigned_delta != expected["assignment_delta"] or selected_delta != expected["selected_delta"]:
            errors.append("contrast_mismatch:" + scenario)
        computed[scenario] = {"assigned_A": a, "assigned_B": b, "A_local_only_descriptive": local,
                              "assignment_delta_A_minus_B": assigned_delta,
                              "selected_delta_A_local_minus_B_descriptive": selected_delta}
    candidate_summaries = doc.get("summaries") or {}
    for scenario, values in computed.items():
        expected_summary = {
            "assigned_policy": {"A": values["assigned_A"], "B": values["assigned_B"]},
            "A_executed_local_only_descriptive": values["A_local_only_descriptive"],
            "A_minus_B_success_rate": values["assignment_delta_A_minus_B"][0],
            "A_minus_B_mean_time": values["assignment_delta_A_minus_B"][1],
            "local_only_minus_B_success_rate_descriptive": values["selected_delta_A_local_minus_B_descriptive"][0],
            "local_only_minus_B_mean_time_descriptive": values["selected_delta_A_local_minus_B_descriptive"][1],
        }
        if candidate_summaries.get(scenario) != expected_summary:
            errors.append("candidate_summary_mismatch:" + scenario)
    reversal = computed.get("selection_reversal", {})
    if not (reversal.get("assignment_delta_A_minus_B") == (-0.5, 0.5)
            and reversal.get("selected_delta_A_local_minus_B_descriptive") == (0.0, -4.0)):
        errors.append("positive_selection_reversal_not_detected")
    null = computed.get("exposure_independent_null", {})
    if null.get("assignment_delta_A_minus_B") != null.get("selected_delta_A_local_minus_B_descriptive"):
        errors.append("null_control_has_selection_discrepancy")
    return {"errors": errors, "rows": len(doc.get("rows", [])), "computed": computed,
            "disposition": "PASS_METHOD_SCOPED" if not errors else "FAIL_AUDIT"}


def corruption_suite(doc):
    mutations = [
        ("drop_failed_fallback_rows", lambda d: d["rows"].__setitem__(slice(None), [r for r in d["rows"] if not (r["scenario"] == "selection_reversal" and r["assigned_arm"] == "A" and r["actual_path"] == "fallback")])),
        ("relabel_post_assignment_as_pre", lambda d: d["rows"][0].update(admission_timing="PRETREATMENT_ELIGIBLE")),
        ("erase_fallback_time", lambda d: [r.update(total_time=0, fallback_time=0) for r in d["rows"] if r["scenario"] == "selection_reversal" and r["assigned_arm"] == "A" and r["actual_path"] == "fallback"]),
        ("promote_selected_subset", lambda d: d.update(estimand_label="LOCAL_EXECUTED_CAUSAL_EFFECT")),
        ("break_null_control", lambda d: d["rows"][-1].update(success=0)),
        ("forge_summary", lambda d: d["summaries"]["selection_reversal"].update(A_minus_B_mean_time=-9)),
    ]
    result = []
    for name, mutate in mutations:
        mutant = copy.deepcopy(doc)
        mutate(mutant)
        result.append({"name": name, "rejected": bool(audit(mutant)["errors"])})
    return result


def main():
    raw = Path(sys.argv[1]).read_bytes()
    doc = json.loads(raw)
    result = audit(doc)
    controls = corruption_suite(doc)
    if not all(c["rejected"] for c in controls):
        result["errors"].append("corruption_control_escaped")
    result["corruptions"] = controls
    result["raw_sha256"] = hashlib.sha256(raw).hexdigest()
    result["disposition"] = "PASS_METHOD_SCOPED" if not result["errors"] else "FAIL_AUDIT"
    print(json.dumps(result, sort_keys=True))
    sys.exit(0 if not result["errors"] else 1)


if __name__ == "__main__":
    main()
