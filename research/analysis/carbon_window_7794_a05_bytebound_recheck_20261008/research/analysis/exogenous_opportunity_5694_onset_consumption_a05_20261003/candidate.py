"""First-failed-boundary classifier using candidate-visible synthetic event times."""
import argparse
import json
from pathlib import Path


def classify(case):
    cue = case["cue_window"]
    if cue is None:
        return "NOT_APPLICABLE", "no_exogenous_opportunity", None, None
    if not case["clock_synchronized"]:
        return "UNKNOWN", "clock_unsynced", None, None
    onset = cue["onset_ms"]
    expiry = cue["expiry_ms"]
    horizon = case["observation_horizon_ms"]
    if horizon < expiry and case["effect_receipt_id"] is None and case["safe_stop_ms"] is None:
        return "UNKNOWN", "right_censored", None, None
    captures = sorted(case["capture_times_ms"])
    acquired_at = next((t for t in captures if onset <= t <= expiry), None)
    if acquired_at is None:
        return "not_acquired", "no_capture_inside_cue_window", None, None
    if case["delivery_ms"] is None or case["delivery_ms"] > expiry:
        return "acquired_not_delivered", "delivery_after_expiry", None, acquired_at
    if case["decision_ms"] is None or case["decision_ms"] > expiry:
        return "delivered_no_decision", "no_decision_before_expiry", None, acquired_at
    if case["safe_stop_ms"] is not None:
        return "decision_no_effect", "safe_stop", None, acquired_at
    receipt = case["effect_receipt_id"]
    if receipt is not None:
        return "eligible_effect", "verified_effect", receipt, acquired_at
    return "decision_no_effect", "no_verified_effect", None, acquired_at


def run(fixture):
    rows = []
    for case in fixture["cases"]:
        boundary, reason, receipt, acquired_at = classify(case)
        rows.append({
            "case_id": case["case_id"],
            "capture_times_ms": list(case["capture_times_ms"]),
            "observation_horizon_ms": case["observation_horizon_ms"],
            "first_acquisition_capture_ms": acquired_at,
            "boundary": boundary,
            "reason": reason,
            "effect_receipt_id": receipt,
        })
    return {
        "schema": "exogenous-opportunity-onset-consumption-raw-v1",
        "fixture_id": fixture["fixture_id"],
        "rows": rows,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixture", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    fixture = json.loads(Path(args.fixture).read_text(encoding="utf-8"))
    raw = run(fixture)
    output = Path(args.out)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(raw, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    print(f"rows={len(raw['rows'])}")
    print("CANDIDATE_COMPLETE")


if __name__ == "__main__":
    main()
