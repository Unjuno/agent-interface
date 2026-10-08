"""Raw-only independent contract audit for Issue #5760 T0."""
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


def avg(values):
    return str(sum((Fraction(str(x)) for x in values), Fraction(0)) / len(values))


def raw_digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def independently_summarize(case):
    rows = case["rows"]
    ids = [row.get("task") for row in rows]
    if ids != TASKS:
        raise ValueError("assignment_denominator_or_order_mismatch")
    local_rows = [r for r in rows if r.get("A_path") == "local"]
    paths = [r.get("A_path") for r in rows]
    if any(path not in ("local", "fallback") for path in paths):
        raise ValueError("invalid_A_exposure_partition")
    if len(local_rows) == 0 or len(paths) != 4:
        raise ValueError("invalid_local_or_total_exposure_count")
    return {
        "case_id": case["case_id"],
        "assigned_n": len(rows),
        "A_assigned_success": avg([r["A_success"] for r in rows]),
        "B_assigned_success": avg([r["B_success"] for r in rows]),
        "A_assigned_mean_total_time": avg([r["A_total_time"] for r in rows]),
        "B_assigned_mean_total_time": avg([r["B_total_time"] for r in rows]),
        "flow": {"local": paths.count("local"), "fallback": paths.count("fallback")},
        "local_n": len(local_rows),
        "local_success": avg([r["A_success"] for r in local_rows]),
        "local_time": avg([r["A_total_time"] for r in local_rows]),
    }


def check_mutation(name, case):
    try:
        actual = independently_summarize(case)
    except (KeyError, ValueError, ZeroDivisionError) as exc:
        return {"mutation": name, "rejected": True, "reason": str(exc)}
    expected = EXPECTED[case["case_id"]]
    return {"mutation": name, "rejected": actual != expected,
            "reason": "frozen_expectation_mismatch" if actual != expected else "ACCEPTED_UNEXPECTEDLY"}


def main():
    # argv: fixture candidate-output oracle-output freeze manifest
    fixture_path, candidate_path, oracle_path, freeze_path, manifest_path = map(Path, sys.argv[1:6])
    data = json.loads(fixture_path.read_text(encoding="utf-8"))
    candidate = json.loads(candidate_path.read_text(encoding="utf-8"))
    oracle = json.loads(oracle_path.read_text(encoding="utf-8"))
    freeze = json.loads(freeze_path.read_text(encoding="utf-8"))
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    errors = []

    if raw_digest(fixture_path) != freeze["artifact_sha256"]["fixtures.json"]:
        errors.append("fixture_sha256_mismatch")
    for name, expected_hash in freeze["artifact_sha256"].items():
        if name in {"fixtures.json", "candidate.py", "oracle.py", "audit.py"}:
            if raw_digest(freeze_path.parent / name) != expected_hash:
                errors.append(name + "_source_sha256_mismatch")
    if manifest.get("allocation") != freeze.get("allocation"):
        errors.append("allocation_identity_mismatch")
    if manifest.get("fixture_sha256") != freeze["artifact_sha256"]["fixtures.json"]:
        errors.append("manifest_fixture_hash_mismatch")
    if candidate.get("schema") != "route_assignment_exposure_candidate_v1":
        errors.append("candidate_schema_invalid")
    if oracle.get("schema") != "route_assignment_exposure_oracle_v1":
        errors.append("oracle_schema_invalid")
    if len(candidate.get("cases", [])) != 2 or len(oracle.get("cases", [])) != 2:
        errors.append("case_count_mismatch")

    direct = []
    for case in data["cases"]:
        got = independently_summarize(case)
        direct.append(got)
        target = EXPECTED.get(case["case_id"])
        if got != target:
            errors.append(case["case_id"] + "_frozen_expectation_mismatch")
        # Compare candidate and separately executed oracle fields to the raw-only reconstruction.
        ccase = next((x for x in candidate.get("cases", []) if x.get("case_id") == case["case_id"]), None)
        ocase = next((x for x in oracle.get("cases", []) if x.get("case_id") == case["case_id"]), None)
        if ccase is None or ocase is None:
            errors.append(case["case_id"] + "_missing_output")
            continue
        for output_name, expected_value in (
            ("assigned_n", got["assigned_n"]),
            ("A_assigned_success", got["A_assigned_success"]),
            ("B_assigned_success", got["B_assigned_success"]),
            ("A_assigned_mean_total_time", got["A_assigned_mean_total_time"]),
            ("B_assigned_mean_total_time", got["B_assigned_mean_total_time"]),
            ("A_local_subset_n", got["local_n"]),
            ("A_local_subset_success", got["local_success"]),
            ("A_local_subset_mean_total_time", got["local_time"]),
        ):
            if ccase.get(output_name) != expected_value or ocase.get(output_name) != expected_value:
                errors.append(case["case_id"] + "_" + output_name + "_candidate_or_oracle_mismatch")
        if ccase.get("A_exposure_flow") != got["flow"] or ocase.get("A_exposure_flow") != got["flow"]:
            errors.append(case["case_id"] + "_exposure_flow_mismatch")
        if ccase.get("local_subset_is_descriptive_only") is not True or ocase.get("local_subset_is_descriptive_only") is not True:
            errors.append(case["case_id"] + "_subset_not_marked_descriptive")

    base = copy.deepcopy(data["cases"][0])
    mutations = []
    dropped = copy.deepcopy(base)
    dropped["rows"] = [r for r in dropped["rows"] if r["A_path"] != "fallback"]
    mutations.append(check_mutation("drop_all_fallback_rows", dropped))
    relabeled = copy.deepcopy(base)
    for row in relabeled["rows"]:
        if row["A_path"] == "fallback":
            row["A_path"] = "local"
    mutations.append(check_mutation("relabel_fallback_as_local", relabeled))
    zeroed = copy.deepcopy(base)
    for row in zeroed["rows"]:
        if row["A_path"] == "fallback":
            row["A_total_time"] = 0
    mutations.append(check_mutation("zero_fallback_total_time", zeroed))
    if not all(x["rejected"] for x in mutations):
        errors.append("one_or_more_mutations_not_rejected")
    if len(direct) != 2:
        errors.append("raw_only_case_count_mismatch")

    report = {
        "schema": "route_assignment_exposure_raw_audit_v1",
        "allocation": freeze["allocation"],
        "decision": "PASS_METHOD_SCOPED" if not errors else "FAIL_T0_CONTRACT",
        "direct_reconstruction": direct,
        "mutations": mutations,
        "candidate_oracle_disagreement_count": sum(1 for x in errors if "candidate_oracle" in x),
        "errors": errors,
        "fixture_sha256": raw_digest(fixture_path),
        "candidate_sha256": raw_digest(candidate_path),
        "oracle_sha256": raw_digest(oracle_path),
    }
    print(json.dumps(report, sort_keys=True, separators=(",", ":")))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
