#!/usr/bin/env python3
"""Finite classifier candidate for Issue #6500; no actual effect is admitted."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


TRUST = "app://trusted.example"
TARGET = "window:12/submit"
RECIPIENT = "object:quarterly-report"
POLICIES = ("VISUAL_ONLY", "SIMILARITY_ALARM", "ORIGIN_BOUND")
CASES = {
    "LEGIT_LOW_RISK": {"captured_origin": TRUST, "dispatch_origin": TRUST, "effect_origin": TRUST,
        "embedded_origin": None, "capture_generation": 7, "dispatch_generation": 7,
        "current_generation": 7, "provenance_complete": True, "pixel_label_match": True,
        "similarity_risk": 0.10, "authorized_target": TARGET, "captured_target": TARGET,
        "dispatch_target": TARGET, "effect_target": TARGET, "intended_recipient": RECIPIENT,
        "effect_recipient": RECIPIENT, "legitimate": True},
    "LEGIT_HIGH_RISK_SCORE": {"captured_origin": TRUST, "dispatch_origin": TRUST, "effect_origin": TRUST,
        "embedded_origin": None, "capture_generation": 7, "dispatch_generation": 7,
        "current_generation": 7, "provenance_complete": True, "pixel_label_match": True,
        "similarity_risk": 0.95, "authorized_target": TARGET, "captured_target": TARGET,
        "dispatch_target": TARGET, "effect_target": TARGET, "intended_recipient": RECIPIENT,
        "effect_recipient": RECIPIENT, "legitimate": True},
    "LOOKALIKE_LOW_RISK_SCORE": {"captured_origin": "app://lookalike.example", "dispatch_origin": "app://lookalike.example",
        "effect_origin": "app://lookalike.example", "embedded_origin": None, "capture_generation": 7,
        "dispatch_generation": 7, "current_generation": 7, "provenance_complete": True,
        "pixel_label_match": True, "similarity_risk": 0.10, "authorized_target": TARGET,
        "captured_target": "window:22/submit", "dispatch_target": "window:22/submit",
        "effect_target": "window:22/submit", "intended_recipient": RECIPIENT,
        "effect_recipient": "object:lookalike-copy", "legitimate": False},
    "WINDOW_REUSE_STALE_GENERATION": {"captured_origin": TRUST, "dispatch_origin": TRUST, "effect_origin": TRUST,
        "embedded_origin": None, "capture_generation": 7, "dispatch_generation": 8,
        "current_generation": 8, "provenance_complete": True, "pixel_label_match": True,
        "similarity_risk": 0.10, "authorized_target": TARGET, "captured_target": TARGET,
        "dispatch_target": TARGET, "effect_target": TARGET, "intended_recipient": RECIPIENT,
        "effect_recipient": RECIPIENT, "legitimate": False},
    "POST_CAPTURE_REPLACEMENT": {"captured_origin": TRUST, "dispatch_origin": "app://lookalike.example",
        "effect_origin": "app://lookalike.example", "embedded_origin": None, "capture_generation": 7,
        "dispatch_generation": 8, "current_generation": 8, "provenance_complete": True,
        "pixel_label_match": True, "similarity_risk": 0.10, "authorized_target": TARGET,
        "captured_target": TARGET, "dispatch_target": "window:22/submit", "effect_target": "window:22/submit",
        "intended_recipient": RECIPIENT, "effect_recipient": "object:lookalike-copy", "legitimate": False},
    "UNKNOWN_PROCESS_PROVENANCE": {"captured_origin": None, "dispatch_origin": None, "effect_origin": None,
        "embedded_origin": None, "capture_generation": 7, "dispatch_generation": 7,
        "current_generation": 7, "provenance_complete": False, "pixel_label_match": True,
        "similarity_risk": 0.10, "authorized_target": TARGET, "captured_target": TARGET,
        "dispatch_target": TARGET, "effect_target": TARGET, "intended_recipient": RECIPIENT,
        "effect_recipient": RECIPIENT, "legitimate": False},
    "UNTRUSTED_EMBEDDED_CONTENT": {"captured_origin": TRUST, "dispatch_origin": TRUST, "effect_origin": TRUST,
        "embedded_origin": "frame://external-content.example", "capture_generation": 7,
        "dispatch_generation": 7, "current_generation": 7, "provenance_complete": True,
        "pixel_label_match": True, "similarity_risk": 0.10, "authorized_target": TARGET,
        "captured_target": TARGET, "dispatch_target": TARGET, "effect_target": TARGET,
        "intended_recipient": RECIPIENT, "effect_recipient": RECIPIENT, "legitimate": False},
    "WRONG_EFFECT_RECIPIENT": {"captured_origin": TRUST, "dispatch_origin": TRUST, "effect_origin": TRUST,
        "embedded_origin": None, "capture_generation": 7, "dispatch_generation": 7,
        "current_generation": 7, "provenance_complete": True, "pixel_label_match": True,
        "similarity_risk": 0.10, "authorized_target": TARGET, "captured_target": TARGET,
        "dispatch_target": TARGET, "effect_target": TARGET, "intended_recipient": RECIPIENT,
        "effect_recipient": "object:other-report", "legitimate": False},
}


def classify(case: dict, policy: str, threshold: float = 0.8) -> tuple[str, bool]:
    if policy == "VISUAL_ONLY":
        allow = case["pixel_label_match"]
        return ("ALLOW" if allow else "REJECT"), allow
    if policy == "SIMILARITY_ALARM":
        allow = case["pixel_label_match"] and case["similarity_risk"] < threshold
        return ("ALLOW" if allow else "ALARM_OR_REJECT"), allow
    if not case["provenance_complete"] or case["capture_generation"] != case["dispatch_generation"] or \
            case["dispatch_generation"] != case["current_generation"]:
        return "UNKNOWN", False
    if case["captured_origin"] != TRUST or case["dispatch_origin"] != TRUST or \
            case["effect_origin"] != TRUST or case["embedded_origin"] not in (None, TRUST) or \
            case["captured_target"] != case["authorized_target"] or \
            case["dispatch_target"] != case["authorized_target"] or \
            case["effect_target"] != case["authorized_target"] or \
            case["effect_recipient"] != case["intended_recipient"]:
        return "MISMATCH", False
    return "MATCH", True


def run() -> dict:
    rows = []
    for case_id, case in CASES.items():
        for policy in POLICIES:
            label, would_admit = classify(case, policy)
            rows.append({"case_id": case_id, **case, "policy": policy,
                         "classification": label, "would_admit": would_admit})
    return {"schema": "origin-effect-binding-6500-candidate-v1", "rows": rows}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("x", encoding="utf-8", newline="\n") as f:
        json.dump(run(), f, sort_keys=True, indent=2)
        f.write("\n")
    print(json.dumps({"rows": 24, "schema": "origin-effect-binding-6500-candidate-v1"}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
