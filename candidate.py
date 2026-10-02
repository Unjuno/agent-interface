"""Offline opportunity-boundary classifier; standard library only."""
import argparse
import json
from pathlib import Path


def classify(episode, opportunity):
    oid = opportunity["id"]
    start, end = opportunity["onset_ms"], opportunity["expiry_ms"]
    if not episode["clock_synced"]:
        return "UNKNOWN", "clock_unsynced", None

    captures = [c for c in episode["captures"] if start <= c["time_ms"] <= end and oid in c["visible_ids"]]
    deliveries = [d for d in episode["deliveries"] if d["opportunity_id"] == oid and start <= d["time_ms"] <= end and any(c["id"] == d["capture_id"] for c in captures)]
    decisions = [p for p in episode["decisions"] if p["opportunity_id"] == oid and start <= p["time_ms"] <= end and any(d["id"] == p["delivery_id"] for d in deliveries)]
    receipts = [r for r in episode["effect_receipts"] if r["opportunity_id"] == oid and start <= r["time_ms"] <= end and any(p["id"] == r["decision_id"] for p in decisions)]

    if receipts:
        return "eligible_effect", "effect_receipt_observed", receipts[0]["id"]
    safe_stops = [p for p in decisions if p["kind"] == "safe_stop"]
    if safe_stops:
        return "decision_no_eligible_effect", "safe_stop", safe_stops[0]["id"]
    if episode["horizon_ms"] < end:
        return "UNKNOWN", "right_censored", None
    if decisions:
        kind = decisions[0]["kind"]
        return "decision_no_eligible_effect", "safe_stop" if kind == "safe_stop" else "no_verified_effect", decisions[0]["id"]
    if deliveries:
        return "delivered_no_decision", "planner_or_queue_boundary", deliveries[0]["id"]
    if captures:
        return "acquired_not_delivered", "delivery_boundary", captures[0]["id"]
    return "not_acquired", "capture_boundary", None


def run(fixture):
    rows = []
    for episode in fixture["episodes"]:
        if not episode["opportunities"]:
            rows.append({"case_id": episode["case_id"], "opportunity_id": None, "boundary": "NOT_APPLICABLE", "detail": "no_exogenous_schedule", "event_id": None})
            continue
        for opportunity in episode["opportunities"]:
            boundary, detail, event_id = classify(episode, opportunity)
            rows.append({"case_id": episode["case_id"], "opportunity_id": opportunity["id"], "boundary": boundary, "detail": detail, "event_id": event_id})
    return rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixture", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    fixture = json.loads(Path(args.fixture).read_text(encoding="utf-8"))
    result = {"allocation_id": fixture["allocation_id"], "rows": run(fixture)}
    Path(args.out).write_text(json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    print(json.dumps({"allocation_id": fixture["allocation_id"], "rows": len(result["rows"]), "status": "CANDIDATE_COMPLETE"}, sort_keys=True))


if __name__ == "__main__":
    main()
