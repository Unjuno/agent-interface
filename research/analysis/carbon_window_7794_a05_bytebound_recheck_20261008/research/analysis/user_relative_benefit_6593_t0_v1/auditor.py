"""Independent reconstruction of all-assigned synthetic benefit contrasts."""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path


def verified(pair_arm: dict) -> bool:
    return (pair_arm.get("required_effect") is True
            and pair_arm.get("forbidden_effect_absent") is True)


def reconstruct(fixture: dict) -> dict:
    cases = []
    for case in fixture["cases"]:
        b = case["benchmark"]
        bvalid = bool(b) and all(x.get("verified") is True for x in b)
        pd = sum(x["agent_s"] - x["standard_human_s"] for x in b) / len(b) if bvalid else None
        contrasts, holds = [], set()
        for p in case["pairs"]:
            assist, control = p["assist"], p["unaided"]
            if assist.get("offered") is not True:
                holds.add("NOT_ASSIGNED")
            elif assist.get("used") is not True:
                holds.add("REFUSED_OR_NOT_USED")
            elif assist.get("config") != p.get("config") or control.get("config") != p.get("config"):
                holds.add("CONFIGURATION_CHANGED")
            elif not verified(assist) or not verified(control):
                holds.add("WRONG_OR_MISSING_EFFECT")
            elif assist.get("elapsed_s") is None or control.get("elapsed_s") is None:
                holds.add("MISSING_TIME")
            else:
                contrasts.append(assist["elapsed_s"] - control["elapsed_s"])
        wd = sum(contrasts) / len(contrasts) if len(contrasts) >= fixture["min_verified_pairs"] else None
        if wd is None:
            if "CONFIGURATION_CHANGED" in holds:
                status = "HOLD_CONFIG_CHANGED"
            elif "WRONG_OR_MISSING_EFFECT" in holds or "MISSING_TIME" in holds:
                status = "HOLD_OUTCOME_OR_TIME"
            elif "REFUSED_OR_NOT_USED" in holds:
                status = "HOLD_REFUSAL_RETAINED"
            else:
                status = "HOLD_INSUFFICIENT_SUPPORT"
        elif pd is None:
            status = "HOLD_BENCHMARK_INCOMPLETE"
        elif pd >= fixture["meaningful_margin_s"] and wd <= -fixture["meaningful_margin_s"]:
            status = "REVERSAL"
        elif ((pd <= -fixture["meaningful_margin_s"] and wd <= -fixture["meaningful_margin_s"])
              or (pd >= fixture["meaningful_margin_s"] and wd >= fixture["meaningful_margin_s"])):
            status = "NO_REVERSAL_SAME_DIRECTION"
        elif abs(pd) < fixture["meaningful_margin_s"] or abs(wd) < fixture["meaningful_margin_s"]:
            status = "NO_MEANINGFUL_DIRECTIONAL_CONTRAST"
        else:
            status = "NO_REVERSAL_OPPOSITE_CASE"
        cases.append({
            "case_id": case["id"],
            "assigned_pair_count": len(case["pairs"]),
            "offer_count": sum(1 for p in case["pairs"] if p["assist"].get("offered") is True),
            "uptake_count": sum(1 for p in case["pairs"] if p["assist"].get("used") is True),
            "valid_matched_pair_count": len(contrasts),
            "pooled_benchmark_delta_s": pd,
            "within_person_delta_s": wd,
            "paired_config_ids": sorted({p["config"] for p in case["pairs"]}),
            "agency_ratings_separate": [p["assist"].get("agency_rating") for p in case["pairs"]],
            "hold_reasons": sorted(holds),
            "verdict": status,
            "assigned_pairs": case["pairs"],
            "benchmark_rows": b,
        })
    return {"allocation": fixture["allocation"], "offer_assignment": fixture["offer_assignment"],
            "case_count": len(cases), "cases": cases}


def audit(fixture: dict, raw: dict) -> dict:
    expected = reconstruct(fixture)
    errors = []
    if raw != expected:
        errors.append("all-assigned-reconstruction-mismatch")
    byid = {c["case_id"]: c for c in raw.get("cases", [])}
    if byid.get("pooled_within_reversal", {}).get("verdict") != "REVERSAL":
        errors.append("planted-direction-reversal-not-recovered")
    if byid.get("same_direction", {}).get("verdict") == "REVERSAL":
        errors.append("null-case-falsely-called-reversal")
    expected_holds = {
        "fast_wrong_effect": "HOLD_OUTCOME_OR_TIME",
        "offer_refusal": "HOLD_REFUSAL_RETAINED",
        "missing_outcome": "HOLD_OUTCOME_OR_TIME",
        "changed_configuration": "HOLD_CONFIG_CHANGED",
        "under_supported": "HOLD_INSUFFICIENT_SUPPORT",
    }
    for case_id, verdict in expected_holds.items():
        if byid.get(case_id, {}).get("verdict") != verdict:
            errors.append(f"invalid-hold-disposition:{case_id}")
    if any(c.get("offer_count") != c.get("assigned_pair_count") for c in raw.get("cases", [])):
        errors.append("assigned-offer-denominator-dropped")
    return {"errors": errors, "cases": len(raw.get("cases", [])),
            "assigned_pairs": sum(c.get("assigned_pair_count", 0) for c in raw.get("cases", [])),
            "reversal_case": byid.get("pooled_within_reversal", {}).get("verdict"),
            "hold_cases": sum(str(c.get("verdict", "")).startswith("HOLD_") for c in raw.get("cases", [])),
            "refused_offers_retained": sum(c.get("offer_count", 0)-c.get("uptake_count", 0) for c in raw.get("cases", []))}


def corrupt(raw: dict, mutation: str) -> dict:
    x = copy.deepcopy(raw)
    byid = {c["case_id"]: c for c in x["cases"]}
    if mutation == "omit_assigned_pair":
        byid["pooled_within_reversal"]["assigned_pairs"].pop()
    elif mutation == "wrong_effect_as_verified":
        for p in byid["fast_wrong_effect"]["assigned_pairs"]:
            p["assist"]["required_effect"] = True
    elif mutation == "refusal_as_use":
        for p in byid["offer_refusal"]["assigned_pairs"]:
            p["assist"]["used"] = True
            p["assist"]["elapsed_s"] = 0
    elif mutation == "missing_as_zero":
        for p in byid["missing_outcome"]["assigned_pairs"]:
            p["assist"]["required_effect"] = True
            p["assist"]["elapsed_s"] = 0
    elif mutation == "erase_config_change":
        for p in byid["changed_configuration"]["assigned_pairs"]:
            p["assist"]["config"] = p["config"]
    elif mutation == "pooled_only_win":
        byid["same_direction"]["verdict"] = "REVERSAL"
    elif mutation == "agency_as_time":
        byid["pooled_within_reversal"]["within_person_delta_s"] = sum(
            p["assist"]["agency_rating"] for p in byid["pooled_within_reversal"]["assigned_pairs"])
    return x


def main() -> None:
    fixture = json.loads(Path(sys.argv[1]).read_text())
    raw = json.loads(Path(sys.argv[2]).read_text())
    result = audit(fixture, raw)
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    raise SystemExit(0 if not result["errors"] else 1)


if __name__ == "__main__":
    main()
