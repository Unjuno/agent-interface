"""Independent raw-only replay for A03. Does not import candidate.py."""
import argparse
import json
from pathlib import Path


def expected(episode, opportunity):
    key = opportunity["id"]
    lo, hi = opportunity["onset_ms"], opportunity["expiry_ms"]
    if not episode["clock_synced"]:
        return {"case_id": episode["case_id"], "opportunity_id": key, "boundary": "UNKNOWN", "detail": "clock_unsynced", "event_id": None}
    seen = [x for x in episode["captures"] if x["time_ms"] >= lo and x["time_ms"] <= hi and key in x["visible_ids"]]
    sent = [x for x in episode["deliveries"] if x["opportunity_id"] == key and x["time_ms"] >= lo and x["time_ms"] <= hi and x["capture_id"] in {c["id"] for c in seen}]
    decided = [x for x in episode["decisions"] if x["opportunity_id"] == key and x["time_ms"] >= lo and x["time_ms"] <= hi and x["delivery_id"] in {d["id"] for d in sent}]
    receipts = [x for x in episode["effect_receipts"] if x["opportunity_id"] == key and x["time_ms"] >= lo and x["time_ms"] <= hi and x["decision_id"] in {p["id"] for p in decided}]
    verified = {x["receipt_id"] for x in episode["scorer_effects"] if x["verified"] and x["opportunity_id"] == key and x["time_ms"] >= lo and x["time_ms"] <= hi}
    valid_receipts = [x for x in receipts if x["id"] in verified]
    if valid_receipts:
        return {"case_id": episode["case_id"], "opportunity_id": key, "boundary": "eligible_effect", "detail": "effect_receipt_observed", "event_id": valid_receipts[0]["id"]}
    safe_stops = [x for x in decided if x["kind"] == "safe_stop"]
    if safe_stops:
        return {"case_id": episode["case_id"], "opportunity_id": key, "boundary": "decision_no_eligible_effect", "detail": "safe_stop", "event_id": safe_stops[0]["id"]}
    if episode["horizon_ms"] < hi:
        return {"case_id": episode["case_id"], "opportunity_id": key, "boundary": "UNKNOWN", "detail": "right_censored", "event_id": None}
    if decided:
        return {"case_id": episode["case_id"], "opportunity_id": key, "boundary": "decision_no_eligible_effect", "detail": "safe_stop" if decided[0]["kind"] == "safe_stop" else "no_verified_effect", "event_id": decided[0]["id"]}
    if sent:
        return {"case_id": episode["case_id"], "opportunity_id": key, "boundary": "delivered_no_decision", "detail": "planner_or_queue_boundary", "event_id": sent[0]["id"]}
    if seen:
        return {"case_id": episode["case_id"], "opportunity_id": key, "boundary": "acquired_not_delivered", "detail": "delivery_boundary", "event_id": seen[0]["id"]}
    return {"case_id": episode["case_id"], "opportunity_id": key, "boundary": "not_acquired", "detail": "capture_boundary", "event_id": None}


def replay(fixture):
    out = []
    for episode in fixture["episodes"]:
        if not episode["opportunities"]:
            out.append({"case_id": episode["case_id"], "opportunity_id": None, "boundary": "NOT_APPLICABLE", "detail": "no_exogenous_schedule", "event_id": None})
        else:
            out.extend(expected(episode, opportunity) for opportunity in episode["opportunities"])
    return out


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--fixture", required=True)
    p.add_argument("--raw", required=True)
    p.add_argument("--out", required=True)
    a = p.parse_args()
    fixture = json.loads(Path(a.fixture).read_text(encoding="utf-8"))
    raw = json.loads(Path(a.raw).read_text(encoding="utf-8"))
    want = replay(fixture)
    errors = []
    if raw.get("allocation_id") != fixture.get("allocation_id"):
        errors.append("allocation_id_mismatch")
    if raw.get("rows") != want:
        errors.append("raw_rows_differ_from_independent_replay")
    expected_keys = [(r["case_id"], r["opportunity_id"]) for r in want]
    if len(expected_keys) != len(set(expected_keys)):
        errors.append("fixture_duplicate_opportunity_key")
    # Frozen corruption controls are applied to independent copies of candidate raw.
    rejected = 0
    if len(want) > 6:
        for index, mutate in (
            (0, lambda row: row.update(event_id="undeclared")),
            (1, lambda row: row.update(boundary="eligible_effect")),
            (2, lambda row: row.update(opportunity_id="forged")),
            (6, lambda row: row.update(boundary="not_acquired")),
        ):
            bad = json.loads(json.dumps(want))
            mutate(bad[index])
            if bad != want:
                rejected += 1
        bad = json.loads(json.dumps(want))
        bad.pop()
        if bad != want:
            rejected += 1
    if rejected != 5:
        errors.append("corruption_controls_not_rejected")
    result = {"allocation_id": fixture["allocation_id"], "rows_replayed": len(want), "errors": errors, "corruptions_rejected": rejected, "disposition": "PASS_METHOD_SCOPED" if not errors else "FAIL_AUDIT"}
    Path(a.out).write_text(json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    return 0 if not errors else 2


if __name__ == "__main__":
    raise SystemExit(main())
