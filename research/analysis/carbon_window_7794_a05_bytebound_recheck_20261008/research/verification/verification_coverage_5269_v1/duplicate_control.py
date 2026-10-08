"""Focused post-formal construction check; does not replay formal allocations."""
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
    base_case = next(row for row in formal["cases"] if row["case_id"] == "iid-baseline")
    required = lower_action(base_case["action"])
    good = copy.deepcopy(required)
    duplicate = copy.deepcopy(good["checks"][0])
    duplicate.update(check_id="optional.target.current.duplicate", criticality="OPTIONAL",
                     dependencies=[])
    good["checks"].append(duplicate)
    accepted = validate_coverage(required, good, {})["status"] == "PLAN_COMPLETE"

    bad = copy.deepcopy(good)
    bad["checks"][-1]["subject_ref"] = required["checks"][0]["subject_ref"]
    try:
        validate_coverage(required, bad, {})
        rejected, reason = False, "accepted"
    except (TypeError, ValueError) as error:
        rejected, reason = True, str(error)
    result = {
        "schema": "verification_coverage_5269_duplicate_construction.v1",
        "allocation": "verification-coverage-5269-duplicate-construction-02",
        "formal_allocation_repeated": False,
        "image": IMAGE,
        "base_case": "iid-baseline",
        "same_primitive_subject_role_new_id_optional": True,
        "nonduplicate_control_accepted": accepted,
        "semantic_duplicate_rejected": rejected and "duplicate or conflicting semantic check" in reason,
        "rejection_reason": reason,
        "coverage_source_sha256": sha(HERE / "coverage.py"),
        "frozen_coverage_source_sha256": "8fd2ede5e300ff2265ee0f427a8476ca5e42795e8c08f2cc304f9d5edee86fd7",
        "parent_formal_sha256": sha(PARENT / "FORMAL-01.json"),
    }
    # Use the immutable v1 coverage digest as a separate source-identity gate.
    result["status"] = ("PASS_TARGETED_CONSTRUCTION"
                        if accepted and rejected and result["coverage_source_sha256"] ==
                        result["frozen_coverage_source_sha256"] else "FAIL_CONSTRUCTION")
    output = Path("/out/DUPLICATE-CONTROL-02.json")
    encoded = json.dumps(result, sort_keys=True, indent=2) + "\n"
    output.write_text(encoded)
    print(json.dumps({"status": result["status"], "nonduplicate_accepted": accepted,
                      "semantic_duplicate_rejected": result["semantic_duplicate_rejected"],
                      "reason": reason,
                      "sha256": hashlib.sha256(encoded.encode()).hexdigest()}, sort_keys=True))


if __name__ == "__main__":
    main()
