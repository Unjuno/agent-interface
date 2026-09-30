"""Raw-only independent checker; deliberately imports no candidate/runner/test module."""

import hashlib
import json
import argparse
from pathlib import Path


ROOT = Path(__file__).resolve().parent
EXPECTED_FILE = ROOT / "oracle_expected.json"
CHECK_FIELDS = {
    "check_id", "primitive", "subject_ref", "criticality",
    "required_evidence_role", "verifier_class", "dependencies", "deadline",
    "budget_class", "fallback",
}


def _expected_doc(row):
    check_id, primitive, subject, criticality, role, verifier, dependencies = row
    return {
        "check_id": check_id,
        "primitive": primitive,
        "subject_ref": subject,
        "criticality": criticality,
        "required_evidence_role": role,
        "verifier_class": verifier,
        "dependencies": dependencies,
        "deadline": None,
        "budget_class": "bounded",
        "fallback": "YIELD_NO_INPUT",
    }


def audit_plan(case_id, ir):
    try:
        expected = json.loads(EXPECTED_FILE.read_text(encoding="utf-8"))[case_id]
        if not isinstance(ir, dict) or set(ir) != {"schema", "unknown_check_required", "checks"}:
            return False
        if ir["schema"] != "verification_ir.v0.1" or type(ir["unknown_check_required"]) is not bool:
            return False
        if type(ir["checks"]) is not list:
            return False
        actual = ir["checks"]
        if any(not isinstance(check, dict) or set(check) != CHECK_FIELDS for check in actual):
            return False
        if actual != [_expected_doc(row) for row in expected]:
            return False
        unknown_expected = any(row[1] == "META.UNKNOWN_REQUIRED" for row in expected)
        return ir["unknown_check_required"] is unknown_expected
    except (KeyError, OSError, ValueError, TypeError):
        return False


def audit_result(result_path="FORMAL-01.json"):
    freeze = json.loads((ROOT / "FREEZE.json").read_text(encoding="utf-8"))
    result = json.loads(Path(result_path).read_text(encoding="utf-8"))
    cases = result["cases"]
    expected_ids = list(json.loads((ROOT / "cases.json").read_text(encoding="utf-8")))
    # The output is compared against the independent case-id set, not candidate-generated plans.
    fixture_ids = [entry["case_id"] for entry in expected_ids]
    if set(result) != {"allocation", "base_sha", "formal_invocation", "case_count", "cases",
                       "source_sha256", "environment", "status"}:
        raise ValueError("formal result fields differ from frozen result contract")
    if result["allocation"] != freeze["allocation"] or result["base_sha"] != freeze["base_sha"]:
        raise ValueError("allocation/base mismatch")
    if result["formal_invocation"] != 1 or result["case_count"] != len(fixture_ids) or \
            result["status"] != "EXECUTED_ONCE_NO_VERDICT_PROMOTION":
        raise ValueError("formal invocation or case count mismatch")
    if [entry["case_id"] for entry in cases] != fixture_ids:
        raise ValueError("case order/identity mismatch")
    for actual, fixture in zip(cases, expected_ids):
        if set(actual) != {"case_id", "action", "ir"} or actual["action"] != fixture["action"]:
            raise ValueError("raw action differs from frozen fixture")
    if any(not audit_plan(entry["case_id"], entry["ir"]) for entry in cases):
        raise ValueError("independent oracle mismatch")
    for path, expected_hash in freeze["source_sha256"].items():
        actual_hash = hashlib.sha256((ROOT / path).read_bytes()).hexdigest()
        if actual_hash != expected_hash or result["source_sha256"].get(path) != expected_hash:
            raise ValueError(f"source hash mismatch: {path}")
    if result["source_sha256"] != freeze["source_sha256"]:
        raise ValueError("source inventory mismatch")
    if result["environment"].get("container_image") != freeze["container_image"]:
        raise ValueError("container image identity mismatch")

    mutations = []
    base = cases[0]["ir"]
    mutations.append(("mandatory_omission", {**base, "checks": base["checks"][:1]}))
    mutations.append(("criticality_downgrade", {**base, "checks": [base["checks"][0],
        {**base["checks"][1], "criticality": "OPTIONAL"}]}))
    mutations.append(("wrong_subject", {**base, "checks": [{**base["checks"][0], "subject_ref": "window:other"},
        base["checks"][1]]}))
    mutations.append(("wrong_role", {**base, "checks": [base["checks"][0],
        {**base["checks"][1], "required_evidence_role": "HISTORICAL_OBSERVATION"}]}))
    mutations.append(("dependency_omission", {**base, "checks": [base["checks"][0],
        {**base["checks"][1], "dependencies": []}]}))
    mutations.append(("unknown_primitive", {**base, "checks": [{**base["checks"][0],
        "primitive": "TARGET.NOVEL"}, base["checks"][1]]}))
    mutations.append(("authority_injection", {**base, "authority": "GRANTED"}))
    unknown_ir = next(row["ir"] for row in cases if row["case_id"] == "unknown-evidence")
    mutations.append(("unknown_marker_suppressed", {**unknown_ir, "unknown_check_required": False}))
    rejected = sum(not audit_plan("unknown-evidence" if label == "unknown_marker_suppressed"
                                  else "iid-baseline", mutated)
                   for label, mutated in mutations)
    if rejected != len(mutations):
        raise ValueError("one or more corruption controls were accepted")
    return {
        "status": "PASS_IR_ORACLE_FINITE_SCOPED",
        "cases": len(cases),
        "checks": sum(len(row["ir"]["checks"]) for row in cases),
        "oracle_disagreements": 0,
        "authority_fields": 0,
        "corruption_controls_rejected": rejected,
        "corruption_controls_total": len(mutations),
        "auditor_imports_candidate": False,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default=None)
    args = parser.parse_args()
    report = audit_result()
    encoded = json.dumps(report, sort_keys=True, indent=2) + "\n"
    if args.out:
        destination = Path(args.out)
        if destination.exists():
            raise SystemExit("refusing to overwrite audit output")
        destination.write_text(encoded, encoding="utf-8")
    else:
        print(encoded, end="")
