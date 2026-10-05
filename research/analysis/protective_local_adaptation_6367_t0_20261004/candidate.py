import argparse
import json
from pathlib import Path


def summarize(offers, events):
    """Describe all offered A/B pairs; never estimate an adapted-only effect."""
    offers_by_id = {row["offer_id"]: row for row in offers}
    events_by_id = {}
    duplicate_event_ids = []
    for row in events:
        offer_id = row.get("offer_id")
        if offer_id in events_by_id:
            duplicate_event_ids.append(offer_id)
        events_by_id[offer_id] = row

    rows = []
    for offer in offers:
        event = events_by_id.get(offer["offer_id"])
        if event is None:
            rows.append({"offer_id": offer["offer_id"], "pair_id": offer["pair_id"],
                         "case_id": offer.get("case_id", offer["pair_id"]),
                         "challenge_id": offer.get("challenge_id"),
                         "arm": offer["arm"], "outcome": None,
                         "cue_fresh": None, "timely_adaptation": False,
                         "occupancy_status": "MISSING", "release_status": "MISSING",
                         "effect_status": "MISSING", "safety_violation": False,
                         "wrong_effects": 0})
            continue
        cue_fresh = event.get("observed_generation") == offer["source_generation"]
        response_ns = event.get("response_ns")
        timely = bool(event.get("adapted")) and cue_fresh and isinstance(response_ns, int) \
            and offer["offered_ns"] <= response_ns <= offer["deadline_ns"]
        effect = event.get("useful_effect") if event.get("effect_status") == "VERIFIED" \
            and isinstance(event.get("useful_effect"), bool) else None
        rows.append({
            "offer_id": offer["offer_id"],
            "pair_id": offer["pair_id"],
            "case_id": offer.get("case_id", offer["pair_id"]),
            "challenge_id": offer.get("challenge_id"),
            "source_generation": offer["source_generation"],
            "arm": offer["arm"],
            "outcome": effect,
            "cue_fresh": cue_fresh,
            "adapted": bool(event.get("adapted")),
            "timely_adaptation": timely,
            "occupancy_status": event.get("occupancy_status", "MISSING"),
            "release_status": event.get("release_status", "MISSING"),
            "effect_status": event.get("effect_status", "MISSING"),
            "safety_violation": bool(event.get("safety_violation"))
            or event.get("wrong_effects", 0) > 0,
            "wrong_effects": event.get("wrong_effects", 0),
            "action_attempted": bool(event.get("action_attempted")),
        })

    pairs = {}
    for row in rows:
        pair = pairs.setdefault(row["pair_id"], {"case_id": row["case_id"],
                                                   "challenge_id": row["challenge_id"]})
        pair[row["arm"]] = row
    pair_rows = []
    for pair_id, arms in sorted(pairs.items()):
        a, b = arms.get("A"), arms.get("B")
        valid_pair = a is not None and b is not None and a["outcome"] is not None \
            and b["outcome"] is not None
        pair_rows.append({
            "pair_id": pair_id,
            "case_id": arms["case_id"],
            "challenge_id": arms["challenge_id"],
            "complete": a is not None and b is not None,
            "A_success": a["outcome"] if a else None,
            "B_success": b["outcome"] if b else None,
            "success_delta_B_minus_A": (int(b["outcome"]) - int(a["outcome"]))
            if valid_pair else None,
        })

    case_rows = []
    for case_id in sorted({row["case_id"] for row in rows}):
        case_offers = [row for row in rows if row["case_id"] == case_id]
        case_pairs = [row for row in pair_rows if row["case_id"] == case_id]
        deltas = [row["success_delta_B_minus_A"] for row in case_pairs
                  if row["success_delta_B_minus_A"] is not None]
        case_delta = sum(deltas) / len(deltas) \
            if case_pairs and len(deltas) == len(case_pairs) else None
        safety = any(row["safety_violation"] or row["release_status"] == "VIOLATION"
                     for row in case_offers)
        missing_effect = any(row["outcome"] is None for row in case_offers)
        evidence_ok = all(row["occupancy_status"] == "VERIFIED"
                          and row["release_status"] == "VERIFIED_EMPTY"
                          and row["cue_fresh"] is not False
                          and (not row.get("adapted") or row["timely_adaptation"])
                          for row in case_offers)
        if safety:
            case_status = "FAIL_SAFETY"
        elif missing_effect:
            case_status = "HOLD_MISSING_EFFECT"
        elif not evidence_ok:
            case_status = "HOLD_MECHANISM_EVIDENCE"
        elif case_delta is None:
            case_status = "HOLD_INCOMPLETE_PAIR"
        elif case_delta > 0:
            case_status = "OBSERVED_ALL_OFFER_B_ADVANTAGE"
        elif case_delta < 0:
            case_status = "OBSERVED_ALL_OFFER_B_DISADVANTAGE"
        else:
            case_status = "NO_DIFFERENCE_ALL_OFFER"
        case_rows.append({"case_id": case_id, "offer_count": len(case_offers),
                          "pair_count": len(case_pairs),
                          "paired_success_delta": case_delta,
                          "status": case_status,
                          "mechanism_evidence_complete": evidence_ok})

    complete_deltas = [row["success_delta_B_minus_A"] for row in pair_rows
                       if row["success_delta_B_minus_A"] is not None]
    delta = sum(complete_deltas) / len(complete_deltas) \
        if pair_rows and len(complete_deltas) == len(pair_rows) else None
    any_safety_violation = any(row["safety_violation"] or row["release_status"] == "VIOLATION"
                               for row in rows)
    missing_effect = any(row["outcome"] is None for row in rows)
    complete_occupancy = all(row["occupancy_status"] == "VERIFIED" for row in rows)
    complete_release = all(row["release_status"] == "VERIFIED_EMPTY" for row in rows)
    generations_valid = all(row["cue_fresh"] is not False for row in rows)
    adaptations_timely = all(not row.get("adapted") or row["timely_adaptation"] for row in rows)
    ledger_complete = len(events_by_id) == len(offers) and not duplicate_event_ids \
        and all(offer_id in offers_by_id for offer_id in events_by_id)

    if any_safety_violation:
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
        "schema_version": 1,
        "offer_count": len(offers),
        "pair_count": len(pair_rows),
        "offers": rows,
        "pairs": pair_rows,
        "cases": case_rows,
        "paired_success_delta": delta,
        "mechanism_attribution_eligible": decision == "DESCRIPTIVE_ALL_OFFER_TOTAL",
        "decision": decision,
        "post_policy_subgroup_effect": None,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("fixture", type=Path)
    parser.add_argument("events", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    fixture = json.loads(args.fixture.read_text())
    events = json.loads(args.events.read_text())
    report = summarize(fixture["offers"], events)
    args.output.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n")
    print(json.dumps({"status": report["decision"], "offers": report["offer_count"],
                      "pairs": report["pair_count"],
                      "paired_success_delta": report["paired_success_delta"]}, sort_keys=True))


if __name__ == "__main__":
    main()
