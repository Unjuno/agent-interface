"""Versioned read-only audit repair; does not execute the candidate or oracle."""
import copy
import hashlib
import json
import sys
from fractions import Fraction
from pathlib import Path

TASKS = ["E1", "E2", "H1", "H2"]
EXPECTED = {
    "selection_reversal": {
        "assigned_n": 4, "A_assigned_success": "1/2", "B_assigned_success": "1",
        "A_assigned_mean_total_time": "11/2", "B_assigned_mean_total_time": "5",
        "flow": {"local": 2, "fallback": 2}, "local_n": 2,
        "local_success": "1", "local_time": "1",
    },
    "null_balanced_exposure": {
        "assigned_n": 4, "A_assigned_success": "1", "B_assigned_success": "1",
        "A_assigned_mean_total_time": "5", "B_assigned_mean_total_time": "5",
        "flow": {"local": 2, "fallback": 2}, "local_n": 2,
        "local_success": "1", "local_time": "5",
    },
}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def avg(xs):
    return str(sum((Fraction(str(x)) for x in xs), Fraction()) / len(xs))


def summarize(case):
    rows = case["rows"]
    ids = [r.get("task") for r in rows]
    if ids != TASKS:
        raise ValueError("assignment_denominator_or_order_mismatch")
    if any(r.get("A_path") not in ("local", "fallback") for r in rows):
        raise ValueError("A_exposure_partition_invalid")
    local = [r for r in rows if r["A_path"] == "local"]
    fallback = [r for r in rows if r["A_path"] == "fallback"]
    if len(local) + len(fallback) != len(rows) or not local:
        raise ValueError("A_exposure_flow_mismatch")
    return {
        "assigned_n": len(rows),
        "A_assigned_success": avg([r["A_success"] for r in rows]),
        "B_assigned_success": avg([r["B_success"] for r in rows]),
        "A_assigned_mean_total_time": avg([r["A_total_time"] for r in rows]),
        "B_assigned_mean_total_time": avg([r["B_total_time"] for r in rows]),
        "flow": {"local": len(local), "fallback": len(fallback)},
        "local_n": len(local),
        "local_success": avg([r["A_success"] for r in local]),
        "local_time": avg([r["A_total_time"] for r in local]),
    }


def project_candidate(row):
    return {
        "assigned_n": row.get("assigned_n"),
        "A_assigned_success": row.get("A_assigned_success"),
        "B_assigned_success": row.get("B_assigned_success"),
        "A_assigned_mean_total_time": row.get("A_assigned_mean_total_time"),
        "B_assigned_mean_total_time": row.get("B_assigned_mean_total_time"),
        "flow": row.get("A_exposure_flow"),
        "local_n": row.get("A_local_subset_n"),
        "local_success": row.get("A_local_subset_success"),
        "local_time": row.get("A_local_subset_mean_total_time"),
    }


def reject_mutation(name, changed, case_id):
    expected = EXPECTED[case_id]
    try:
        observed = summarize(changed)
    except (KeyError, ValueError, ZeroDivisionError) as exc:
        return {"mutation": name, "rejected": True, "reason": str(exc)}
    mismatch = observed != expected
    return {"mutation": name, "rejected": mismatch,
            "reason": "frozen_estimand_mismatch" if mismatch else "ACCEPTED_UNEXPECTEDLY"}


def main():
    root = Path(__file__).resolve().parent
    fixture_path, candidate_path, oracle_path, audit_v1_path, freeze_path = map(Path, sys.argv[1:6])
    data = json.loads(fixture_path.read_text(encoding="utf-8"))
    candidate = json.loads(candidate_path.read_text(encoding="utf-8"))
    oracle = json.loads(oracle_path.read_text(encoding="utf-8"))
    audit_v1 = json.loads(audit_v1_path.read_text(encoding="utf-8"))
    freeze = json.loads(freeze_path.read_text(encoding="utf-8"))
    errors, reconstructions = [], []

    for name, wanted in freeze["input_sha256"].items():
        if sha(root / name) != wanted:
            errors.append(name + "_sha256_mismatch")
    for name, wanted in freeze["source_sha256"].items():
        if sha(root / name) != wanted:
            errors.append(name + "_source_sha256_mismatch")
    if freeze.get("candidate_oracle_invocations_v2") != 0:
        errors.append("v2_candidate_oracle_rerun_declared")
    if audit_v1.get("decision") != "FAIL_T0_CONTRACT" or audit_v1.get("errors") != [
            "selection_reversal_frozen_expectation_mismatch",
            "null_balanced_exposure_frozen_expectation_mismatch"]:
        errors.append("v1_failure_record_mismatch")
    if [c.get("case_id") for c in data["cases"]] != list(EXPECTED):
        errors.append("fixture_case_inventory_mismatch")

    for case in data["cases"]:
        cid = case["case_id"]
        observed = summarize(case)
        reconstructions.append({"case_id": cid, **observed})
        if observed != EXPECTED[cid]:
            errors.append(cid + "_frozen_numeric_expectation_mismatch")
        candidate_row = next((r for r in candidate.get("cases", []) if r.get("case_id") == cid), None)
        oracle_row = next((r for r in oracle.get("cases", []) if r.get("case_id") == cid), None)
        if candidate_row is None or oracle_row is None:
            errors.append(cid + "_missing_candidate_or_oracle_case")
        elif project_candidate(candidate_row) != observed or project_candidate(oracle_row) != observed:
            errors.append(cid + "_candidate_or_oracle_disagreement")
        if candidate_row and candidate_row.get("local_subset_is_descriptive_only") is not True:
            errors.append(cid + "_candidate_subset_label_missing")
        if oracle_row and oracle_row.get("local_subset_is_descriptive_only") is not True:
            errors.append(cid + "_oracle_subset_label_missing")

    selection = copy.deepcopy(data["cases"][0])
    dropped = copy.deepcopy(selection)
    dropped["rows"] = [r for r in dropped["rows"] if r["A_path"] != "fallback"]
    relabeled = copy.deepcopy(selection)
    for row in relabeled["rows"]:
        if row["A_path"] == "fallback":
            row["A_path"] = "local"
    zeroed = copy.deepcopy(selection)
    for row in zeroed["rows"]:
        if row["A_path"] == "fallback":
            row["A_total_time"] = 0
    mutations = [
        reject_mutation("drop_all_fallback_rows", dropped, "selection_reversal"),
        reject_mutation("relabel_fallback_as_local", relabeled, "selection_reversal"),
        reject_mutation("zero_fallback_total_time", zeroed, "selection_reversal"),
    ]
    if not all(item["rejected"] for item in mutations):
        errors.append("mutation_control_not_rejected")

    report = {
        "schema": "route_assignment_exposure_raw_audit_v2",
        "allocation": freeze["allocation"],
        "decision": "PASS_AUDIT_V2_REPAIR_SCOPED" if not errors else "HOLD_AUDIT_V2_INTEGRITY",
        "candidate_invocations_v2": 0,
        "oracle_invocations_v2": 0,
        "audit_v1_preserved": True,
        "v1_decision": audit_v1.get("decision"),
        "direct_reconstructions": reconstructions,
        "mutations": mutations,
        "errors": errors,
        "fixture_sha256": sha(fixture_path),
        "candidate_stdout_sha256": sha(candidate_path),
        "oracle_stdout_sha256": sha(oracle_path),
        "audit_v1_stdout_sha256": sha(audit_v1_path),
    }
    print(json.dumps(report, sort_keys=True, separators=(",", ":")))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())

