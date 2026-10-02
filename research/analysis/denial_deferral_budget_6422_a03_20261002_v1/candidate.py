import argparse
import json
from pathlib import Path


LABEL = "FRESH_APPROVAL_AFTER_STATED_DEFERRAL"


def eligible(case, fixture):
    return (
        case["source_principal"] in fixture["required_principals"]
        and case["source_stated"] is True
        and case["verified_by"] == "independent_receipt"
        and case["predicate"] == fixture["condition"]["predicate"]
        and case["evidence_kind"] == fixture["condition"]["evidence_requirement"]
        and bool(case["scope_key"])
        and case["scope_key"] == case["budget_key"]
    )


def decision(case, fixture, bounded):
    if case["safety_release"]:
        return {"decision": "ALLOW_SAFETY_RELEASE", "fresh_request": None, "effect_authorized": False,
                "post_presentations": case["prior_presentations"], "post_consumed_evidence_ids": case["consumed_evidence_ids"]}
    if not eligible(case, fixture):
        return {"decision": "HOLD_DEFERRAL_NOT_ELIGIBLE", "fresh_request": None, "effect_authorized": False,
                "post_presentations": case["prior_presentations"], "post_consumed_evidence_ids": case["consumed_evidence_ids"]}
    if bounded and case["evidence_id"] in case["consumed_evidence_ids"]:
        return {"decision": "HOLD_EVIDENCE_ALREADY_CONSUMED", "fresh_request": None, "effect_authorized": False,
                "post_presentations": case["prior_presentations"], "post_consumed_evidence_ids": case["consumed_evidence_ids"]}
    if bounded and case["prior_presentations"] >= fixture["max_fresh_requests"]:
        return {"decision": "HOLD_BUDGET_EXHAUSTED", "fresh_request": None, "effect_authorized": False,
                "post_presentations": case["prior_presentations"], "post_consumed_evidence_ids": case["consumed_evidence_ids"]}
    count = case["prior_presentations"] + 1
    consumed = sorted(set(case["consumed_evidence_ids"]) | ({case["evidence_id"]} if bounded else set()))
    return {"decision": "ASK_FRESH_APPROVAL", "fresh_request": {"label": LABEL, "scope_key": case["scope_key"],
            "request_id": case["request_id"], "evidence_id": case["evidence_id"]},
            "effect_authorized": False, "post_presentations": count, "post_consumed_evidence_ids": consumed}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    fixture = json.loads(Path(args.input).read_text(encoding="utf-8"))
    rows = [{"case_id": case["case_id"], "case": case,
             "unbounded": decision(case, fixture, False), "bounded": decision(case, fixture, True)}
            for case in fixture["cases"]]
    Path(args.output).write_text(json.dumps({"schema": "denial-deferral-budget-a03-raw-v1", "rows": rows},
                                            indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
