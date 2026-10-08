#!/usr/bin/env python3
"""Independent raw-only replay for issue #5665 T1."""
import json
import sys
from pathlib import Path


LABELS = ["F0", "F1", "F2", "F3", "F4", "F5", "F6", "F7"]
WEIGHTS = [500, 250, 120, 60, 30, 20, 10, 10]
MASS = {label: weight / sum(WEIGHTS) for label, weight in zip(LABELS, WEIGHTS)}
K = 20
ERRORS = []


def disposition(row):
    training = row["train"]
    training_units = row["train_unit_ids"]
    valid = row["validation"]
    valid_units = row["validation_unit_ids"]
    if row["train_planned_n"] != len(training) + row["train_unknown_n"] or row["train_unknown_n"] != 0:
        return "HOLD_NO_ELIGIBLE_DENOMINATOR"
    if row["validation_planned_n"] != len(valid) + row["validation_unknown_n"] or row["validation_unknown_n"] != 0:
        return "HOLD_NO_ELIGIBLE_DENOMINATOR"
    if len(training_units) != len(training) or len(set(training_units)) != len(training_units):
        return "HOLD_NONEXCHANGEABLE"
    if len(valid_units) != len(valid) or len(set(valid_units)) != len(valid_units):
        return "HOLD_NONEXCHANGEABLE"
    if row["train_taxonomy"] != row["validation_taxonomy"]:
        return "HOLD_TAXONOMY_UNSTABLE"
    if row["train_stratum"] != row["validation_stratum"]:
        return "HOLD_NONEXCHANGEABLE"
    return "ELIGIBLE_IID"


def replay(row):
    seen = set(row["train"])
    frequencies = {label: row["train"].count(label) for label in seen}
    singleton_count = sum(value == 1 for value in frequencies.values())
    estimate = singleton_count / len(row["train"])
    tail_seen = set(row["train"][:-K])
    tail_new = 0
    for label in row["train"][-K:]:
        if label not in tail_seen:
            tail_new += 1
            tail_seen.add(label)
    tail_estimate = tail_new / K
    true_mass = sum(probability for label, probability in MASS.items() if label not in seen)
    observed_new = sum(label not in seen for label in row["validation"]) / len(row["validation"])
    return {
        "n": len(row["train"]),
        "f1": singleton_count,
        "gt_prediction": estimate,
        "last_k_prediction": tail_estimate,
        "true_missing_mass": true_mass,
        "validation_new_rate": observed_new,
        "gt_abs_error_to_truth": abs(estimate - true_mass),
        "last_k_abs_error_to_truth": abs(tail_estimate - true_mass),
        "gt_abs_error_to_validation": abs(estimate - observed_new),
        "last_k_abs_error_to_validation": abs(tail_estimate - observed_new),
    }


def close(a, b):
    return abs(a - b) <= 1e-12


def audit(rows):
    if len(rows) != 204:
        ERRORS.append(f"row_count:{len(rows)}")
    if len({row.get("case_id") for row in rows}) != len(rows):
        ERRORS.append("duplicate_case_id")
    iid = sorted((row for row in rows if row.get("kind") == "iid"), key=lambda row: row["seed"])
    if len(iid) != 200 or [row["seed"] for row in iid] != list(range(5_665_001, 5_665_201)):
        ERRORS.append("iid_seed_schedule")

    comparisons = {"gt_truth": [], "last_k_truth": [], "gt_validation": [], "last_k_validation": []}
    for row in rows:
        if row.get("schema") != "issue5665-t1-raw-v1":
            ERRORS.append(f"schema:{row.get('case_id')}")
            continue
        if row["train_planned_n"] != len(row["train"]) + row["train_unknown_n"]:
            ERRORS.append(f"train_denominator:{row['case_id']}")
        if row["validation_planned_n"] != len(row["validation"]) + row["validation_unknown_n"]:
            ERRORS.append(f"validation_denominator:{row['case_id']}")
        got = disposition(row)
        if got != row["candidate"].get("disposition"):
            ERRORS.append(f"disposition:{row['case_id']}:{got}")
        if got != "ELIGIBLE_IID":
            continue
        expected = replay(row)
        for key, value in expected.items():
            actual = row["candidate"].get(key)
            if isinstance(value, float):
                if not isinstance(actual, (int, float)) or not close(actual, value):
                    ERRORS.append(f"metric:{row['case_id']}:{key}")
            elif actual != value:
                ERRORS.append(f"metric:{row['case_id']}:{key}")
        if row["kind"] == "iid":
            comparisons["gt_truth"].append(expected["gt_abs_error_to_truth"])
            comparisons["last_k_truth"].append(expected["last_k_abs_error_to_truth"])
            comparisons["gt_validation"].append(expected["gt_abs_error_to_validation"])
            comparisons["last_k_validation"].append(expected["last_k_abs_error_to_validation"])

    controls = {}
    base = next((dict(row) for row in iid if row["kind"] == "iid"), None)
    if base is None:
        ERRORS.append("mutation_setup_missing")
    else:
        duplicate = json.loads(json.dumps(base))
        duplicate["train"].append(duplicate["train"][0])
        duplicate["train_unit_ids"].append(duplicate["train_unit_ids"][0])
        duplicate["train_planned_n"] += 1
        controls["correlated_duplicate_rejected"] = disposition(duplicate) == "HOLD_NONEXCHANGEABLE"

        missing = json.loads(json.dumps(base))
        missing["train"].pop()
        controls["missing_denominator_rejected"] = disposition(missing) == "HOLD_NO_ELIGIBLE_DENOMINATOR"

        taxonomy = json.loads(json.dumps(base))
        taxonomy["validation_taxonomy"] = "failure-taxonomy-v2"
        controls["taxonomy_drift_held"] = disposition(taxonomy) == "HOLD_TAXONOMY_UNSTABLE"

        shift = json.loads(json.dumps(base))
        shift["validation_stratum"] = "synthetic-shifted-generator-v1"
        controls["distribution_shift_held"] = disposition(shift) == "HOLD_NONEXCHANGEABLE"
    if not all(controls.values()) or len(controls) != 4:
        ERRORS.append("mutation_controls")

    means = {name: (sum(values) / len(values) if values else None) for name, values in comparisons.items()}
    eligible_iid = [row for row in iid if disposition(row) == "ELIGIBLE_IID"]
    if len(eligible_iid) != 200:
        ERRORS.append(f"iid_eligibility_count:{len(eligible_iid)}")
    decision = {
        "method_controls_pass": not ERRORS and len(controls) == 4 and all(controls.values()),
        "gt_beats_last_k_on_exact_missing_mass": (means["gt_truth"] < means["last_k_truth"] if means["gt_truth"] is not None else False),
        "gt_beats_last_k_on_finite_validation": (means["gt_validation"] < means["last_k_validation"] if means["gt_validation"] is not None else False),
        "iid_replicates": len(eligible_iid),
    }
    return {"audit": "PASS" if not ERRORS else "FAIL", "rows": len(rows),
            "eligible_iid_rows": len(eligible_iid), "scheduled_iid_rows": len(iid),
            "held_control_rows": len(rows) - len(iid),
            "errors": ERRORS, "mutation_controls": controls,
            "mean_absolute_errors": means, "decision": decision}


if __name__ == "__main__":
    raw_path = Path(sys.argv[1])
    records = [json.loads(line) for line in raw_path.read_text(encoding="utf-8").splitlines() if line]
    result = audit(records)
    print(json.dumps(result, sort_keys=True, indent=2))
    raise SystemExit(0 if result["audit"] == "PASS" else 1)


