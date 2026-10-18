import argparse
import json
from pathlib import Path


def audit(fixture, events, report):
    findings = []
    offers = fixture["offers"]
    scheduled = {row["offer_id"]: row for row in offers}
    observed = {}
    for event in events:
        offer_id = event.get("offer_id")
        if offer_id in observed:
            findings.append("DUPLICATE_EVENT_ID")
        observed[offer_id] = event
        if offer_id not in scheduled:
            findings.append("UNSCHEDULED_EVENT")
    if len(events) != len(offers) or set(observed) != set(scheduled):
        findings.append("EVENT_CARDINALITY_MISMATCH")

    report_offers = {row.get("offer_id"): row for row in report.get("offers", [])}
    if len(report_offers) != len(report.get("offers", [])) or set(report_offers) != set(scheduled):
        findings.append("REPORT_OFFER_CARDINALITY_MISMATCH")

    by_pair = {}
    by_case = {}
    for offer_id, offer in scheduled.items():
        event = observed.get(offer_id)
        result = report_offers.get(offer_id)
        if event is None or result is None:
            continue
        identity = (offer.get("pair_id"), offer.get("arm"), offer.get("case_id"),
                    offer.get("challenge_id"))
        event_identity = (event.get("pair_id"), event.get("arm"),
                          event.get("case_id", offer.get("case_id")),
                          event.get("challenge_id", offer.get("challenge_id")))
        if identity != event_identity:
            findings.append("OFFER_IDENTITY_MISMATCH")
        expected_case = fixture.get("expected_cases", {}).get(
            offer.get("case_id", offer["pair_id"]))
        if event.get("observed_generation") != offer.get("source_generation") \
                and expected_case != "HOLD_MECHANISM_EVIDENCE":
            findings.append("SOURCE_GENERATION_MISMATCH")
        expected_effect = event.get("useful_effect") if event.get("effect_status") == "VERIFIED" \
            and isinstance(event.get("useful_effect"), bool) else None
        if result.get("outcome") != expected_effect \
                or result.get("release_status") != event.get("release_status") \
                or result.get("effect_status") != event.get("effect_status"):
            findings.append("RELEASE_OR_EFFECT_MISMATCH")
        if result.get("source_generation") != offer.get("source_generation") \
                or result.get("cue_fresh") != (event.get("observed_generation")
                                                 == offer.get("source_generation")):
            findings.append("SOURCE_GENERATION_MISMATCH")
        if "adapted_success_rate" in report or report.get("post_policy_subgroup_effect") not in (None,):
            findings.append("POST_POLICY_SUBGROUP_ESTIMAND_PRESENT")
        case_id = offer.get("case_id", offer["pair_id"])
        by_pair.setdefault(offer["pair_id"], {"case_id": case_id,
                                                "challenge_id": offer.get("challenge_id")})[
                                                    offer["arm"]] = (offer, event)
        by_case.setdefault(case_id, []).append((offer, event))

    expected_pairs = []
    for pair_id, arms in sorted(by_pair.items()):
        a, b = arms.get("A"), arms.get("B")
        if a is None or b is None:
            findings.append("UNPAIRED_OFFER")
            delta = None
        else:
            oa, ea = a
            ob, eb = b
            if oa.get("challenge_id") != ob.get("challenge_id"):
                findings.append("CHALLENGE_NOT_MATCHED")
            va = ea.get("useful_effect") if ea.get("effect_status") == "VERIFIED" \
                and isinstance(ea.get("useful_effect"), bool) else None
            vb = eb.get("useful_effect") if eb.get("effect_status") == "VERIFIED" \
                and isinstance(eb.get("useful_effect"), bool) else None
            delta = int(vb) - int(va) if va is not None and vb is not None else None
        expected_pairs.append({"pair_id": pair_id, "case_id": arms["case_id"],
                               "challenge_id": arms["challenge_id"],
                               "complete": a is not None and b is not None,
                               "A_success": a[1].get("useful_effect")
                               if a and a[1].get("effect_status") == "VERIFIED"
                               and isinstance(a[1].get("useful_effect"), bool) else None,
                               "B_success": b[1].get("useful_effect")
                               if b and b[1].get("effect_status") == "VERIFIED"
                               and isinstance(b[1].get("useful_effect"), bool) else None,
                               "success_delta_B_minus_A": delta})
    if report.get("pairs") != expected_pairs:
        findings.append("PAIR_RECONSTRUCTION_MISMATCH")
    deltas = [row["success_delta_B_minus_A"] for row in expected_pairs
              if row["success_delta_B_minus_A"] is not None]
    aggregate = sum(deltas) / len(deltas) \
        if expected_pairs and len(deltas) == len(expected_pairs) else None
    if report.get("paired_success_delta") != aggregate:
        findings.append("ALL_OFFER_EFFECT_MISMATCH")
    if report.get("offer_count") != len(offers) or report.get("pair_count") != len(expected_pairs):
        findings.append("DENOMINATOR_MISMATCH")

    expected_cases = {}
    for case_id, case_rows in sorted(by_case.items()):
        pair_rows = [row for row in expected_pairs if row["case_id"] == case_id]
        case_deltas = [row["success_delta_B_minus_A"] for row in pair_rows
                       if row["success_delta_B_minus_A"] is not None]
        case_delta = sum(case_deltas) / len(case_deltas) \
            if pair_rows and len(case_deltas) == len(pair_rows) else None
        safety = any(event.get("safety_violation")
                     or event.get("release_status") == "VIOLATION"
                     or event.get("wrong_effects", 0) > 0 for _, event in case_rows)
        missing_effect = any(event.get("effect_status") != "VERIFIED"
                             or not isinstance(event.get("useful_effect"), bool)
                             for _, event in case_rows)
        evidence_ok = all(event.get("occupancy_status") == "VERIFIED"
                          and event.get("release_status") == "VERIFIED_EMPTY"
                          and event.get("observed_generation") == offer.get("source_generation")
                          and (not event.get("adapted") or
                               isinstance(event.get("response_ns"), int)
                               and offer.get("offered_ns", 0) <= event["response_ns"]
                               <= offer.get("deadline_ns", -1))
                          for offer, event in case_rows)
        if safety:
            status = "FAIL_SAFETY"
        elif missing_effect:
            status = "HOLD_MISSING_EFFECT"
        elif not evidence_ok:
            status = "HOLD_MECHANISM_EVIDENCE"
        elif case_delta is None:
            status = "HOLD_INCOMPLETE_PAIR"
        elif case_delta > 0:
            status = "OBSERVED_ALL_OFFER_B_ADVANTAGE"
        elif case_delta < 0:
            status = "OBSERVED_ALL_OFFER_B_DISADVANTAGE"
        else:
            status = "NO_DIFFERENCE_ALL_OFFER"
        expected_cases[case_id] = status
    reported_cases = {row.get("case_id"): row.get("status") for row in report.get("cases", [])}
    if reported_cases != expected_cases:
        findings.append("CASE_CLASSIFICATION_MISMATCH")
    if expected_cases != fixture.get("expected_cases", {}):
        findings.append("FROZEN_ORACLE_DISAGREEMENT")

    return {"status": "PASS_AUDIT" if not findings else "FAIL_AUDIT",
            "findings": sorted(set(findings)),
            "offer_count": len(offers),
            "event_count": len(events),
            "pair_count": len(expected_pairs),
            "case_statuses": expected_cases}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("fixture", type=Path)
    parser.add_argument("events", type=Path)
    parser.add_argument("candidate", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    fixture = json.loads(args.fixture.read_text())
    events = json.loads(args.events.read_text())
    report = json.loads(args.candidate.read_text())
    result = audit(fixture, events, report)
    args.output.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    print(json.dumps(result, sort_keys=True))
    return 0 if result["status"] == "PASS_AUDIT" else 1


if __name__ == "__main__":
    raise SystemExit(main())
