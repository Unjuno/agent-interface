"""Corrected focused check: base plan is positive, duplicate plan negative."""
import copy
import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
PARENT = HERE.parent / "verification_ir_5268_v1"
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(PARENT))

from candidate import lower_action  # noqa: E402
from coverage import validate_coverage  # noqa: E402

IMAGE = "python:3.12-slim@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    formal = json.loads((PARENT / "FORMAL-01.json").read_text())
    case = next(row for row in formal["cases"] if row["case_id"] == "iid-baseline")
    required = lower_action(case["action"])
    baseline = copy.deepcopy(required)
    positive = validate_coverage(required, baseline, {})
    duplicate_plan = copy.deepcopy(baseline)
    duplicate = copy.deepcopy(duplicate_plan["checks"][0])
    duplicate.update(check_id="optional.target.current.duplicate",
                     criticality="OPTIONAL", dependencies=[])
    duplicate_plan["checks"].append(duplicate)
    try:
        validate_coverage(required, duplicate_plan, {})
        rejected, reason = False, "accepted"
    except (TypeError, ValueError) as error:
        rejected, reason = True, str(error)
    same_key = (duplicate["primitive"], duplicate["subject_ref"],
                duplicate["required_evidence_role"]) == (
                    baseline["checks"][0]["primitive"], baseline["checks"][0]["subject_ref"],
                    baseline["checks"][0]["required_evidence_role"])
    coverage_sha = sha(HERE / "coverage.py")
    frozen_sha = "8fd2ede5e300ff2265ee0f427a8476ca5e42795e8c08f2cc304f9d5edee86fd7"
    status = ("PASS_TARGETED_CONSTRUCTION" if positive["status"] == "PLAN_COMPLETE" and
              same_key and rejected and "duplicate or conflicting semantic check" in reason and
              coverage_sha == frozen_sha else "FAIL_CONSTRUCTION")
    result = {
        "schema": "verification_coverage_5269_duplicate_construction.v2",
        "allocation": "verification-coverage-5269-duplicate-construction-03",
        "formal_allocation_repeated": False,
        "image": IMAGE,
        "base_case": "iid-baseline",
        "baseline_positive_control": positive["status"],
        "duplicate_new_id_optional_same_primitive_subject_role": same_key,
        "semantic_duplicate_rejected": rejected,
        "rejection_reason": reason,
        "coverage_source_sha256": coverage_sha,
        "frozen_coverage_source_sha256": frozen_sha,
        "parent_formal_sha256": sha(PARENT / "FORMAL-01.json"),
        "prior_construction_02_failure_preserved": True,
        "status": status,
    }
    encoded = json.dumps(result, sort_keys=True, indent=2) + "\n"
    Path("/out/DUPLICATE-CONTROL-03.json").write_text(encoded)
    print(json.dumps({"status": status, "positive": positive["status"],
                      "duplicate_rejected": rejected, "reason": reason,
                      "sha256": hashlib.sha256(encoded.encode()).hexdigest()}, sort_keys=True))


if __name__ == "__main__":
    main()
