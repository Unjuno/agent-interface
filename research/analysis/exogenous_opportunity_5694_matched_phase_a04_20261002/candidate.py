"""Candidate first-failed-boundary classifier for the frozen synthetic fixture."""
import argparse
import json
from pathlib import Path


def classify(case):
    opp = case["opportunity"]
    if opp is None:
        return "NOT_APPLICABLE", "no_exogenous_opportunity", None
    if not case["clock_synchronized"]:
        return "UNKNOWN", "clock_unsynced", None
    expiry = opp["expiry_ms"]
    horizon = case["observation_horizon_ms"]
    captures = case["captures"]
    acquired = any(case["opportunity_id"] in cap["opportunity_ids"] for cap in captures)
    if horizon < expiry and not case["effect_receipt_id"] and case["safe_stop_ms"] is None:
        return "UNKNOWN", "right_censored", None
    if not acquired:
        return "not_acquired", "no_capture_before_expiry", None
    delivery = case["delivery_ms"]
    if delivery is None or delivery > expiry:
        return "acquired_not_delivered", "delivery_after_expiry", None
    decision = case["decision_ms"]
    if decision is None or decision > expiry:
        return "delivered_no_decision", "no_decision_before_expiry", None
    if case["safe_stop_ms"] is not None:
        return "decision_no_effect", "safe_stop", None
    receipt = case["effect_receipt_id"]
    if receipt:
        return "eligible_effect", "verified_effect", receipt
    return "decision_no_effect", "no_verified_effect", None


def run(fixture):
    rows = []
    for case in fixture["cases"]:
        boundary, reason, receipt = classify(case)
        rows.append({
            "case_id": case["case_id"],
            "capture_schedule_ms": list(case["capture_schedule_ms"]),
            "observation_horizon_ms": case["observation_horizon_ms"],
            "boundary": boundary,
            "reason": reason,
            "effect_receipt_id": receipt,
        })
    return {"schema":"first-failed-boundary-raw-v1", "fixture_id":fixture["fixture_id"], "rows":rows}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixture", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    fixture = json.loads(Path(args.fixture).read_text(encoding="utf-8"))
    raw = run(fixture)
    Path(args.out).write_text(json.dumps(raw, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    print(f"rows={len(raw['rows'])}")
    print("CANDIDATE_COMPLETE")


if __name__ == "__main__":
    main()
