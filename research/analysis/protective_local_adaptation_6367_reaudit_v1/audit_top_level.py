import argparse
import json
from pathlib import Path


def reconstruct_decision(offers, events):
    scheduled = {row["offer_id"]: row for row in offers}
    observed = {}
    duplicate_ids = set()
    for event in events:
        offer_id = event.get("offer_id")
        if offer_id in observed:
            duplicate_ids.add(offer_id)
        observed[offer_id] = event

    rows = []
    for offer in offers:
        event = observed.get(offer["offer_id"])
        fresh = event is not None and event.get("observed_generation") \
            == offer["source_generation"]
        effect = event is not None and event.get("effect_status") == "VERIFIED" \
            and isinstance(event.get("useful_effect"), bool)
        response = event.get("response_ns") if event is not None else None
        timely = bool(event and event.get("adapted")) and fresh \
            and isinstance(response, int) \
            and offer["offered_ns"] <= response <= offer["deadline_ns"]
        rows.append((offer, event, fresh, effect, timely))

    safety_violation = any(
        event.get("safety_violation")
        or event.get("release_status") == "VIOLATION"
        or event.get("wrong_effects", 0) > 0
        for event in events)
    ledger_complete = len(events) == len(offers) \
        and len(observed) == len(offers) \
        and len(scheduled) == len(offers) \
        and not duplicate_ids and set(observed) == set(scheduled)
    missing_effect = any(not effect for _, event, _, effect, _ in rows)
    complete_occupancy = all(event is not None
                             and event.get("occupancy_status") == "VERIFIED"
                             for _, event, _, _, _ in rows)
    complete_release = all(event is not None
                           and event.get("release_status") == "VERIFIED_EMPTY"
                           for _, event, _, _, _ in rows)
    generations_valid = all(fresh for _, _, fresh, _, _ in rows)
    adaptations_timely = all(event is not None
                             and (not bool(event.get("adapted")) or timely)
                             for _, event, _, _, timely in rows)

    if safety_violation:
        decision = "FAIL_SAFETY"
    elif not ledger_complete:
        decision = "HOLD_INCOMPLETE_LEDGER"
    elif missing_effect:
        decision = "HOLD_MISSING_EFFECT"
    elif not complete_occupancy or not complete_release or not generations_valid \
            or not adaptations_timely:
        decision = "HOLD_MECHANISM_EVIDENCE"
    else:
        decision = "DESCRIPTIVE_ALL_OFFER_TOTAL"
    return {
        "decision": decision,
        "mechanism_attribution_eligible": decision == "DESCRIPTIVE_ALL_OFFER_TOTAL",
    }


def audit_top_level(fixture, events, report):
    expected = reconstruct_decision(fixture["offers"], events)
    mismatches = [key for key, value in expected.items()
                  if type(report.get(key)) is not type(value) or report.get(key) != value]
    return {
        "status": "PASS_TOP_LEVEL_AUDIT" if not mismatches else "FAIL_TOP_LEVEL_AUDIT",
        "mismatches": mismatches,
        "expected": expected,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("fixture", type=Path)
    parser.add_argument("events", type=Path)
    parser.add_argument("report", type=Path)
    args = parser.parse_args()
    result = audit_top_level(
        json.loads(args.fixture.read_text()),
        json.loads(args.events.read_text()),
        json.loads(args.report.read_text()),
    )
    print(json.dumps(result, sort_keys=True))
    return 0 if result["status"] == "PASS_TOP_LEVEL_AUDIT" else 1


if __name__ == "__main__":
    raise SystemExit(main())
