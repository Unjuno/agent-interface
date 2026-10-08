"""Deterministic candidate for Issue #6519's finite T0 method check."""
import json
import sys
from pathlib import Path


def evaluate(case, arm, supported_modes):
    card = case["card"]
    source_ok = card["observation"] == case["observation"]
    surface_ok = card["surface"] == case["surface"]
    generation_ok = card["generation"] == case["generation"]
    mode_ok = card["mode"] in supported_modes and card["mode"] == case["raw_mode"]
    valid = source_ok and surface_ok and generation_ok and mode_ok
    row = {
        "case_id": case["id"], "arm": arm,
        "binding": {"observation": case["observation"], "surface": case["surface"], "generation": case["generation"]},
        "mode": "UNKNOWN", "effect_claim": "UNKNOWN", "effect_claim_status": "UNVERIFIED", "operations": [],
        "evidence_refs": [], "confidence": "NONE", "uncertainty": "UNKNOWN",
        "goal_appropriateness": "UNKNOWN", "authority": False,
        "completion": "NONE", "unknown": True, "raw_evidence_available": case["raw_available"],
    }
    if arm == "RAW_ONLY":
        return row
    if not valid:
        if arm == "SUPPRESS_UNKNOWN":
            row["unknown"] = False
        if arm == "HIDE_RAW_EVIDENCE":
            row["raw_evidence_available"] = False
        if arm == "CARD_AS_AUTHORITY":
            row["authority"] = True
        return row

    row["unknown"] = False
    row["mode"] = card["mode"]
    row["binding"] = {"observation": case["observation"], "surface": case["surface"], "generation": case["generation"]}
    row["uncertainty"] = "synthetic_checks_consistent"
    row["confidence"] = card["confidence"]
    if arm == "MODE_LABEL":
        return row
    if arm in ("CANDIDATE_EFFECT", "UNCERTAINTY_CONTRADICTION", "DROP_SOURCE_BINDING", "FLIP_EFFECT_LABEL", "SUPPRESS_UNKNOWN", "CARD_AS_AUTHORITY", "HIDE_RAW_EVIDENCE"):
        row["effect_claim"] = card["effect"]
        row["operations"] = list(card["operations"])
        row["evidence_refs"] = list(card["evidence"])
    if arm == "CANDIDATE_EFFECT":
        return row
    if arm == "UNCERTAINTY_CONTRADICTION":
        row["uncertainty"] = "no_local_binding_or_mode_conflict_detected"
        return row
    if arm == "DROP_SOURCE_BINDING":
        row["binding"] = {"observation": None, "surface": card["surface"], "generation": card["generation"]}
    elif arm == "FLIP_EFFECT_LABEL":
        row["effect_claim"] = "save_complete" if card["effect"] != "save_complete" else "unknown"
    elif arm == "CARD_AS_AUTHORITY":
        row["authority"] = True
    elif arm == "HIDE_RAW_EVIDENCE":
        row["raw_evidence_available"] = False
    return row


def run(fixture):
    return {"schema": "issue-6519-t0-raw-v1", "rows": [
        evaluate(case, arm, fixture["supported_modes"])
        for case in fixture["cases"] for arm in fixture["arms"]
    ]}


def main(argv):
    if len(argv) != 3:
        raise SystemExit("usage: candidate.py FIXTURE.json OUTPUT.json")
    fixture = json.loads(Path(argv[1]).read_text(encoding="utf-8"))
    result = run(fixture)
    Path(argv[2]).write_text(json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main(sys.argv)
