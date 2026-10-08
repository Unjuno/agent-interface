"""Emit a synthetic all-assigned ledger and scoped pooled/within contrasts."""
from __future__ import annotations

import json
import sys
from pathlib import Path


def outcome_ok(row: dict) -> bool:
    return row.get("required_effect") is True and row.get("forbidden_effect_absent") is True


def summarize(case: dict, fixture: dict) -> dict:
    bench = case["benchmark"]
    benchmark_complete = all(r["verified"] is True for r in bench)
    pooled_delta = (sum(r["agent_s"] - r["standard_human_s"] for r in bench) / len(bench)
                    if benchmark_complete and bench else None)
    pairs = case["pairs"]
    usable = []
    reasons = set()
    for pair in pairs:
        a, h = pair["assist"], pair["unaided"]
        if not a["offered"]:
            reasons.add("NOT_ASSIGNED")
        elif not a["used"]:
            reasons.add("REFUSED_OR_NOT_USED")
        elif a["config"] != pair["config"] or h["config"] != pair["config"]:
            reasons.add("CONFIGURATION_CHANGED")
        elif not outcome_ok(a) or not outcome_ok(h):
            reasons.add("WRONG_OR_MISSING_EFFECT")
        elif a["elapsed_s"] is None or h["elapsed_s"] is None:
            reasons.add("MISSING_TIME")
        else:
            usable.append(a["elapsed_s"] - h["elapsed_s"])
    if len(usable) < fixture["min_verified_pairs"]:
        within_delta = None
        if "CONFIGURATION_CHANGED" in reasons:
            verdict = "HOLD_CONFIG_CHANGED"
        elif "WRONG_OR_MISSING_EFFECT" in reasons or "MISSING_TIME" in reasons:
            verdict = "HOLD_OUTCOME_OR_TIME"
        elif "REFUSED_OR_NOT_USED" in reasons:
            verdict = "HOLD_REFUSAL_RETAINED"
        else:
            verdict = "HOLD_INSUFFICIENT_SUPPORT"
    else:
        within_delta = sum(usable) / len(usable)
        margin = fixture["meaningful_margin_s"]
        if pooled_delta is None:
            verdict = "HOLD_BENCHMARK_INCOMPLETE"
        elif pooled_delta >= margin and within_delta <= -margin:
            verdict = "REVERSAL"
        elif (pooled_delta <= -margin and within_delta <= -margin) or (pooled_delta >= margin and within_delta >= margin):
            verdict = "NO_REVERSAL_SAME_DIRECTION"
        elif (abs(pooled_delta) < margin or abs(within_delta) < margin):
            verdict = "NO_MEANINGFUL_DIRECTIONAL_CONTRAST"
        else:
            verdict = "NO_REVERSAL_OPPOSITE_CASE"
    return {
        "case_id": case["id"],
        "assigned_pair_count": len(pairs),
        "offer_count": sum(p["assist"]["offered"] is True for p in pairs),
        "uptake_count": sum(p["assist"]["used"] is True for p in pairs),
        "valid_matched_pair_count": len(usable),
        "pooled_benchmark_delta_s": pooled_delta,
        "within_person_delta_s": within_delta,
        "paired_config_ids": sorted({p["config"] for p in pairs}),
        "agency_ratings_separate": [p["assist"]["agency_rating"] for p in pairs],
        "hold_reasons": sorted(reasons),
        "verdict": verdict,
        "assigned_pairs": pairs,
        "benchmark_rows": bench,
    }


def run(fixture: dict) -> dict:
    rows = [summarize(c, fixture) for c in fixture["cases"]]
    return {"allocation": fixture["allocation"], "offer_assignment": fixture["offer_assignment"],
            "case_count": len(rows), "cases": rows}


def main() -> None:
    fixture = json.loads(Path(sys.argv[1]).read_text())
    raw = run(fixture)
    Path(sys.argv[2]).write_text(json.dumps(raw, sort_keys=True, separators=(",", ":")) + "\n")
    print(json.dumps({"allocation": raw["allocation"], "cases": raw["case_count"],
                      "assigned_pairs": sum(r["assigned_pair_count"] for r in raw["cases"])}, sort_keys=True))


if __name__ == "__main__":
    main()
