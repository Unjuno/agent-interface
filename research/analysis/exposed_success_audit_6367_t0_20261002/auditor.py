#!/usr/bin/env python3
"""Independent standard-library-only raw audit for Issue #6367 T0."""

import argparse
import hashlib
import json
from pathlib import Path

FROZEN_INPUTS = {
    "primary.json": "6b46db2d58a4ecfdd6214bcb9779e6447d34fe448b6dc58706b7579a0a806f0d",
    "selection_trap.json": "e74130346924f40d7b51bcb80731e9c8cb0cb49df1e4d6caf407a8a73481a067",
}


def _independent_classification(offer, row, generation):
    if row is None:
        return {"classification": "UNKNOWN_MISSING_ARM_ROW", "eligible_success": None}

    danger = row.get("safety") or {}
    release = row.get("release") or {}
    if danger.get("forbidden_effect") is True or danger.get("release_violation") is True or release.get("verified_neutral") is False:
        return {"classification": "FAIL_SAFETY", "eligible_success": False}
    if row.get("source_generation") != generation:
        return {"classification": "UNKNOWN_SOURCE_GENERATION", "eligible_success": None}
    if row.get("challenge_id") != offer.get("challenge_id"):
        return {"classification": "UNKNOWN_NONCOMPARABLE_CHALLENGE", "eligible_success": None}

    change = row.get("adaptation") or {}
    if change.get("triggered") is True and (
        change.get("fresh") is not True or change.get("cue_generation") != offer.get("challenge_generation")
    ):
        return {"classification": "INVALID_ADAPTATION_PROVENANCE", "eligible_success": False}

    effect = row.get("effect") or {}
    if effect.get("independent") is not True or type(effect.get("success")) is not bool:
        return {"classification": "UNKNOWN_EFFECT_EVIDENCE", "eligible_success": None}
    occupancy = row.get("occupancy") or {}
    down, up = occupancy.get("down_ms"), occupancy.get("up_ms")
    if occupancy.get("qualified") is not True or type(down) is not int or type(up) is not int or down < 0 or up < down:
        return {"classification": "UNKNOWN_PHYSICAL_OCCUPANCY", "eligible_success": None}
    if release.get("verified_neutral") is not True:
        return {"classification": "UNKNOWN_RELEASE_EVIDENCE", "eligible_success": None}
    if type(row.get("deadline_met")) is not bool:
        return {"classification": "UNKNOWN_DEADLINE_EVIDENCE", "eligible_success": None}

    passed = effect["success"] is True and row["deadline_met"] is True
    return {
        "classification": "VERIFIED_SUCCESS" if passed else "VERIFIED_NON_SUCCESS",
        "eligible_success": passed,
    }


def _reconstruct(fixture):
    if fixture.get("schema") != "agent-interface/exposed-success-ledger-v1":
        raise ValueError("unsupported fixture schema")
    assigned = fixture.get("offers")
    if not isinstance(assigned, list) or not assigned:
        raise ValueError("no assigned offers")
    ids = [entry.get("offer_id") for entry in assigned]
    if any(not isinstance(value, str) or not value for value in ids) or len(ids) != len(set(ids)):
        raise ValueError("invalid or duplicate offer identity")

    arms = fixture.get("arms") or {}
    per_offer = {}
    summaries = {}
    denominators = {}
    for arm in ("fixed", "adaptive"):
        raw_arm = arms.get(arm) or {}
        denominators[arm] = len(assigned)
        summary = {"offers": len(assigned), "verified_successes": 0, "verified_non_successes": 0, "unknowns": 0, "safety_failures": 0}
        for offer in assigned:
            offer_id = offer["offer_id"]
            row = _independent_classification(offer, raw_arm.get(offer_id), fixture.get("schedule_generation"))
            per_offer.setdefault(offer_id, {})[arm] = row
            key = {
                "VERIFIED_SUCCESS": "verified_successes",
                "VERIFIED_NON_SUCCESS": "verified_non_successes",
                "FAIL_SAFETY": "safety_failures",
            }.get(row["classification"], "unknowns")
            summary[key] += 1
        summary["success_rate"] = summary["verified_successes"] / summary["offers"]
        summaries[arm] = summary

    spill = {
        arm: sorted(set((arms.get(arm) or {}) ) - set(ids))
        for arm in ("fixed", "adaptive")
    }
    hard_failure = any(summaries[arm]["safety_failures"] > 0 for arm in summaries)
    incomplete = any(summaries[arm]["unknowns"] > 0 for arm in summaries) or any(spill.values())
    if hard_failure:
        decision = "FAIL_SAFETY"
    elif incomplete:
        decision = "HOLD_INCOMPLETE_EVIDENCE"
    else:
        gap = summaries["adaptive"]["success_rate"] - summaries["fixed"]["success_rate"]
        decision = "PLANTED_BENEFIT_DETECTED" if gap > 0 else "NULL_ALL_OFFER_EFFECT" if gap == 0 else "ADAPTIVE_LOWER_ALL_OFFER_EFFECT"

    triggered = 0
    trigger_successes = 0
    for offer in assigned:
        offer_id = offer["offer_id"]
        raw = (arms.get("adaptive") or {}).get(offer_id) or {}
        if (raw.get("adaptation") or {}).get("triggered") is True:
            triggered += 1
            if per_offer[offer_id]["adaptive"]["classification"] == "VERIFIED_SUCCESS":
                trigger_successes += 1

    return {
        "fixture_id": fixture.get("fixture_id"),
        "denominators": denominators,
        "offers": per_offer,
        "arms": summaries,
        "extra_rows": spill,
        "post_policy_diagnostic": {
            "adaptive_triggered_opportunities": triggered,
            "adaptive_triggered_successes": trigger_successes,
            "primary_estimand": "all_assigned_offers_policy_assignment",
        },
        "conditioning_warning": triggered < len(assigned),
        "decision": decision,
    }


def audit(fixture_bytes, result_bytes, expected_fixture_sha256):
    errors = []
    observed_hash = hashlib.sha256(fixture_bytes).hexdigest()
    if observed_hash != expected_fixture_sha256:
        errors.append("INPUT_SHA256_MISMATCH")
    try:
        fixture = json.loads(fixture_bytes)
        claimed = json.loads(result_bytes)
        reconstructed = _reconstruct(fixture)
    except (UnicodeDecodeError, json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        return {"status": "FAIL_AUDIT", "errors": errors + ["RAW_PARSE_OR_SCHEMA_ERROR:" + type(exc).__name__]}
    if claimed != reconstructed:
        errors.append("CANDIDATE_SUMMARY_MISMATCH")
    return {
        "status": "PASS_METHOD_ONLY" if not errors else "FAIL_AUDIT",
        "errors": errors,
        "fixture_id": reconstructed["fixture_id"],
        "input_sha256": observed_hash,
        "reconstructed_decision": reconstructed["decision"],
        "reconstructed_denominators": reconstructed["denominators"],
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("fixture_dir", type=Path)
    parser.add_argument("candidate_dir", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    findings = []
    for filename, expected_hash in FROZEN_INPUTS.items():
        input_bytes = (args.fixture_dir / filename).read_bytes()
        result_bytes = (args.candidate_dir / (Path(filename).stem + ".result.json")).read_bytes()
        findings.append(audit(input_bytes, result_bytes, expected_hash))
    errors = [error for item in findings for error in item["errors"]]
    report = {"status": "PASS_METHOD_ONLY" if not errors else "FAIL_AUDIT", "errors": errors, "fixtures": findings}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "errors": len(errors), "fixtures": len(findings)}, sort_keys=True))
    return 0 if report["status"] == "PASS_METHOD_ONLY" else 1


if __name__ == "__main__":
    raise SystemExit(main())
