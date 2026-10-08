"""Preflight-tested read-only audit of immutable #5760 T0 raw outputs."""
import copy
import hashlib
import json
import sys
from fractions import Fraction
from pathlib import Path

TASKS = ["E1", "E2", "H1", "H2"]
EXPECTED = {
    "selection_reversal": {"assigned_n": 4, "A_assigned_success": "1/2", "B_assigned_success": "1",
        "A_assigned_mean_total_time": "11/2", "B_assigned_mean_total_time": "5",
        "flow": {"local": 2, "fallback": 2}, "local_n": 2, "local_success": "1", "local_time": "1"},
    "null_balanced_exposure": {"assigned_n": 4, "A_assigned_success": "1", "B_assigned_success": "1",
        "A_assigned_mean_total_time": "5", "B_assigned_mean_total_time": "5",
        "flow": {"local": 2, "fallback": 2}, "local_n": 2, "local_success": "1", "local_time": "5"},
}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def avg(values):
    return str(sum((Fraction(str(v)) for v in values), Fraction()) / len(values))


def summarize(case):
    rows = case["rows"]
    if [r.get("task") for r in rows] != TASKS:
        raise ValueError("assignment_denominator_or_order_mismatch")
    paths = [r.get("A_path") for r in rows]
    if any(p not in ("local", "fallback") for p in paths):
        raise ValueError("A_exposure_partition_invalid")
    local = [r for r in rows if r["A_path"] == "local"]
    fallback = [r for r in rows if r["A_path"] == "fallback"]
    if len(local) + len(fallback) != 4 or not local:
        raise ValueError("A_exposure_flow_invalid")
    return {
        "assigned_n": 4,
        "A_assigned_success": avg([r["A_success"] for r in rows]),
        "B_assigned_success": avg([r["B_success"] for r in rows]),
        "A_assigned_mean_total_time": avg([r["A_total_time"] for r in rows]),
        "B_assigned_mean_total_time": avg([r["B_total_time"] for r in rows]),
        "flow": {"local": len(local), "fallback": len(fallback)},
        "local_n": len(local),
        "local_success": avg([r["A_success"] for r in local]),
        "local_time": avg([r["A_total_time"] for r in local]),
    }


def candidate_projection(row):
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


def rejects_mutation(case):
    try:
        return summarize(case) != EXPECTED[case["case_id"]]
    except (KeyError, ValueError, ZeroDivisionError):
        return True


def run_audit(root, freeze):
    errors = []
    for name, wanted in freeze["input_sha256"].items():
        if sha(root / name) != wanted:
            errors.append(name + "_sha256_mismatch")
    for name, wanted in freeze["source_sha256"].items():
        if sha(root / name) != wanted:
            errors.append(name + "_source_sha256_mismatch")
    if freeze.get("candidate_oracle_invocations_v3") != 0:
        errors.append("v3_candidate_oracle_rerun_declared")
    if freeze.get("audit_v3_invocations") != 1 or not freeze.get("audit_allocation"):
        errors.append("v3_allocation_schema_invalid")

    data = json.loads((root / "fixtures.json").read_text(encoding="utf-8"))
    candidate = json.loads((root / "candidate.stdout.json").read_text(encoding="utf-8"))
    oracle = json.loads((root / "oracle.stdout.json").read_text(encoding="utf-8"))
    first_audit = json.loads((root / "audit.stdout.json").read_text(encoding="utf-8"))
    first_exec = json.loads((root / "EXECUTION.json").read_text(encoding="utf-8"))
    audit2_exec = json.loads((root / "AUDIT_V2_EXECUTION.json").read_text(encoding="utf-8"))
    audit2_stdout = (root / "audit_v2.stdout.txt").read_text(encoding="utf-8")
    if first_audit.get("decision") != "FAIL_T0_CONTRACT" or first_audit.get("errors") != [
            "selection_reversal_frozen_expectation_mismatch", "null_balanced_exposure_frozen_expectation_mismatch"]:
        errors.append("audit_v1_failure_not_preserved")
    if [x.get("count") for x in first_exec.get("invocations", [])[:2]] != [1, 1]:
        errors.append("original_candidate_oracle_counts_invalid")
    if audit2_exec.get("disposition") != "STOP_AUDIT_V2_CONFIGURATION_MISMATCH" or "KeyError('allocation')" not in audit2_exec.get("error", ""):
        errors.append("audit_v2_stop_not_preserved")
    if "KeyError: 'allocation'" not in audit2_stdout:
        errors.append("audit_v2_stdout_does_not_match_receipt")

    direct = []
    for case in data.get("cases", []):
        cid = case["case_id"]
        value = summarize(case)
        direct.append({"case_id": cid, **value})
        if value != EXPECTED.get(cid):
            errors.append(cid + "_frozen_expectation_mismatch")
        c_row = next((r for r in candidate.get("cases", []) if r.get("case_id") == cid), None)
        o_row = next((r for r in oracle.get("cases", []) if r.get("case_id") == cid), None)
        if c_row is None or o_row is None or candidate_projection(c_row) != value or candidate_projection(o_row) != value:
            errors.append(cid + "_candidate_or_oracle_mismatch")
        if c_row and c_row.get("local_subset_is_descriptive_only") is not True:
            errors.append(cid + "_candidate_subset_label_missing")
        if o_row and o_row.get("local_subset_is_descriptive_only") is not True:
            errors.append(cid + "_oracle_subset_label_missing")

    original = copy.deepcopy(data["cases"][0])
    dropped = copy.deepcopy(original)
    dropped["rows"] = [r for r in dropped["rows"] if r["A_path"] != "fallback"]
    relabeled = copy.deepcopy(original)
    for row in relabeled["rows"]:
        if row["A_path"] == "fallback":
            row["A_path"] = "local"
    zeroed = copy.deepcopy(original)
    for row in zeroed["rows"]:
        if row["A_path"] == "fallback":
            row["A_total_time"] = 0
    mutations = [{"name": name, "rejected": rejects_mutation(case)} for name, case in [
        ("drop_all_fallback_rows", dropped), ("relabel_fallback_as_local", relabeled), ("zero_fallback_total_time", zeroed)]]
    if not all(m["rejected"] for m in mutations):
        errors.append("mutation_control_not_rejected")
    return {
        "schema": "route_assignment_exposure_audit_v3",
        "audit_allocation": freeze["audit_allocation"],
        "decision": "PASS_AUDIT_V3_REPAIR_SCOPED" if not errors else "HOLD_AUDIT_V3_INTEGRITY",
        "candidate_invocations_v3": 0,
        "oracle_invocations_v3": 0,
        "audit_v1_preserved": True,
        "audit_v2_stop_preserved": True,
        "direct_reconstructions": direct,
        "mutations": mutations,
        "errors": errors,
        "fixture_sha256": sha(root / "fixtures.json"),
        "candidate_stdout_sha256": sha(root / "candidate.stdout.json"),
        "oracle_stdout_sha256": sha(root / "oracle.stdout.json"),
        "audit_v1_stdout_sha256": sha(root / "audit.stdout.json"),
        "audit_v2_stdout_sha256": sha(root / "audit_v2.stdout.txt"),
    }


def main():
    root = Path(__file__).resolve().parent
    fixture, candidate, oracle, audit1, audit2, freeze_path = map(Path, sys.argv[1:7])
    # Fixed paths are also hashed; positional arguments must match the frozen inputs.
    expected_args = ["fixtures.json", "candidate.stdout.json", "oracle.stdout.json", "audit.stdout.json", "audit_v2.stdout.txt", "FREEZE_AUDIT_V3.json"]
    if [p.name for p in (fixture, candidate, oracle, audit1, audit2, freeze_path)] != expected_args:
        print(json.dumps({"decision": "HOLD_AUDIT_V3_INTEGRITY", "errors": ["input_argument_order_mismatch"]}, separators=(",", ":")))
        return 1
    freeze = json.loads(freeze_path.read_text(encoding="utf-8"))
    result = run_audit(root, freeze)
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0 if not result["errors"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
