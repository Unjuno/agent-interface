#!/usr/bin/env python3
"""Research-only exposed-success ledger candidate for Issue #6367 T0."""

import argparse
import json
from pathlib import Path


def _classify(offer, row, schedule_generation):
    if row is None:
        return {"classification": "UNKNOWN_MISSING_ARM_ROW", "eligible_success": None}

    safety = row.get("safety") or {}
    release = row.get("release") or {}
    if safety.get("forbidden_effect") is True or safety.get("release_violation") is True or release.get("verified_neutral") is False:
        return {"classification": "FAIL_SAFETY", "eligible_success": False}

    if row.get("source_generation") != schedule_generation:
        return {"classification": "UNKNOWN_SOURCE_GENERATION", "eligible_success": None}
    if row.get("challenge_id") != offer.get("challenge_id"):
        return {"classification": "UNKNOWN_NONCOMPARABLE_CHALLENGE", "eligible_success": None}

    adaptation = row.get("adaptation") or {}
    if adaptation.get("triggered") is True and (
        adaptation.get("fresh") is not True
        or adaptation.get("cue_generation") != offer.get("challenge_generation")
    ):
        return {"classification": "INVALID_ADAPTATION_PROVENANCE", "eligible_success": False}

    effect = row.get("effect") or {}
    if effect.get("independent") is not True or not isinstance(effect.get("success"), bool):
        return {"classification": "UNKNOWN_EFFECT_EVIDENCE", "eligible_success": None}

    occupancy = row.get("occupancy") or {}
    down, up = occupancy.get("down_ms"), occupancy.get("up_ms")
    if occupancy.get("qualified") is not True or type(down) is not int or type(up) is not int:
        return {"classification": "UNKNOWN_PHYSICAL_OCCUPANCY", "eligible_success": None}
    if down < 0 or up < down:
        return {"classification": "UNKNOWN_PHYSICAL_OCCUPANCY", "eligible_success": None}
    if release.get("verified_neutral") is not True:
        return {"classification": "UNKNOWN_RELEASE_EVIDENCE", "eligible_success": None}
    if not isinstance(row.get("deadline_met"), bool):
        return {"classification": "UNKNOWN_DEADLINE_EVIDENCE", "eligible_success": None}

    success = effect["success"] and row["deadline_met"]
    return {
        "classification": "VERIFIED_SUCCESS" if success else "VERIFIED_NON_SUCCESS",
        "eligible_success": success,
    }


def evaluate(fixture):
    if fixture.get("schema") != "agent-interface/exposed-success-ledger-v1":
        raise ValueError("unsupported fixture schema")
    offers = fixture.get("offers")
    if not isinstance(offers, list) or not offers:
        raise ValueError("schedule must contain at least one assigned offer")
    offer_ids = [offer.get("offer_id") for offer in offers]
    if any(not isinstance(offer_id, str) or not offer_id for offer_id in offer_ids) or len(set(offer_ids)) != len(offer_ids):
        raise ValueError("assigned offer ids must be unique non-empty strings")

    arms = fixture.get("arms") or {}
    result_rows = {}
    summaries = {}
    denominators = {}
    for arm_name in ("fixed", "adaptive"):
        arm = arms.get(arm_name) or {}
        denominators[arm_name] = len(offers)
        result_rows[arm_name] = {}
        counts = {"offers": len(offers), "verified_successes": 0, "verified_non_successes": 0, "unknowns": 0, "safety_failures": 0}
        for offer in offers:
            offer_id = offer["offer_id"]
            classified = _classify(offer, arm.get(offer_id), fixture.get("schedule_generation"))
            result_rows[arm_name][offer_id] = classified
            classification = classified["classification"]
            if classification == "VERIFIED_SUCCESS":
                counts["verified_successes"] += 1
            elif classification == "VERIFIED_NON_SUCCESS":
                counts["verified_non_successes"] += 1
            elif classification == "FAIL_SAFETY":
                counts["safety_failures"] += 1
            else:
                counts["unknowns"] += 1
        counts["success_rate"] = counts["verified_successes"] / counts["offers"]
        summaries[arm_name] = counts

    extra_rows = {
        arm: sorted(set((arms.get(arm) or {}).keys()) - set(offer_ids))
        for arm in ("fixed", "adaptive")
    }
    unsafe = any(summaries[arm]["safety_failures"] for arm in summaries)
    unknown = any(summaries[arm]["unknowns"] for arm in summaries) or any(extra_rows.values())
    if unsafe:
        decision = "FAIL_SAFETY"
    elif unknown:
        decision = "HOLD_INCOMPLETE_EVIDENCE"
    else:
        difference = summaries["adaptive"]["success_rate"] - summaries["fixed"]["success_rate"]
        decision = "PLANTED_BENEFIT_DETECTED" if difference > 0 else "NULL_ALL_OFFER_EFFECT" if difference == 0 else "ADAPTIVE_LOWER_ALL_OFFER_EFFECT"

    adaptive_rows = result_rows["adaptive"]
    triggered_count = 0
    triggered_successes = 0
    for offer in offers:
        offer_id = offer["offer_id"]
        raw_row = (arms.get("adaptive") or {}).get(offer_id) or {}
        if (raw_row.get("adaptation") or {}).get("triggered") is True:
            triggered_count += 1
            if adaptive_rows[offer_id]["classification"] == "VERIFIED_SUCCESS":
                triggered_successes += 1
    conditioning_warning = triggered_count < len(offers)
    return {
        "fixture_id": fixture.get("fixture_id"),
        "denominators": denominators,
        "offers": {
            offer["offer_id"]: {
                arm: result_rows[arm][offer["offer_id"]]
                for arm in ("fixed", "adaptive")
            }
            for offer in offers
        },
        "arms": summaries,
        "extra_rows": extra_rows,
        "post_policy_diagnostic": {
            "adaptive_triggered_opportunities": triggered_count,
            "adaptive_triggered_successes": triggered_successes,
            "primary_estimand": "all_assigned_offers_policy_assignment",
        },
        "conditioning_warning": conditioning_warning,
        "decision": decision,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input_dir", type=Path)
    parser.add_argument("output_dir", type=Path)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    summary = []
    for filename in ("primary.json", "selection_trap.json"):
        fixture = json.loads((args.input_dir / filename).read_text(encoding="utf-8"))
        result = evaluate(fixture)
        output = args.output_dir / (Path(filename).stem + ".result.json")
        output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        summary.append({"fixture_id": result["fixture_id"], "decision": result["decision"], "denominators": result["denominators"]})
    print(json.dumps(summary, sort_keys=True))


if __name__ == "__main__":
    main()
