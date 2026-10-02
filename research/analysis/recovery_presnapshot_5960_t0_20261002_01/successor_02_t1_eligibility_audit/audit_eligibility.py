"""Apply Issue #5960's frozen T1 gates to cited retained-candidate summaries."""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
GATES = ("case_level_pre_post_evidence", "source_clock", "independent_cause_label",
         "eligible_safe_slack_failure", "diagnosis_or_reproducer_utility_outcome")


def audit(inputs):
    inventory = inputs.get("inventory", [])
    eligible = []
    errors = []
    ids = [row.get("id") for row in inventory]
    if len(ids) != len(set(ids)):
        errors.append("duplicate candidate id")
    for row in inventory:
        missing = [gate for gate in GATES if row.get(gate) is not True]
        if not missing:
            eligible.append(row["id"])
    return {"schema": "issue5960-t1-eligibility-result-v1",
            "status": "ELIGIBLE_COHORT_FOUND" if eligible and not errors else
                      ("FAIL_AUDIT" if errors else "HOLD_NO_ELIGIBLE_RETAINED_COHORT"),
            "candidate_count": len(inventory), "eligible_count": len(eligible),
            "eligible_ids": eligible, "errors": errors,
            "scope": "bounded cited-candidate inventory only; not an exhaustive assertion about all remote issues or branches"}


def main():
    inputs = json.loads((HERE / "eligibility_inputs.json").read_text(encoding="utf-8"))
    result = audit(inputs)
    (HERE / "audit_result.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    raise SystemExit(0 if result["status"] == "HOLD_NO_ELIGIBLE_RETAINED_COHORT" else 1)


if __name__ == "__main__":
    main()
