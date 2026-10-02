#!/usr/bin/env python3
"""Independent raw table reconstruction; intentionally does not import candidate.py."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path


APP = "app://trusted.example"
TARGET = "window:12/submit"
OBJECT = "object:quarterly-report"
POLICIES = ("VISUAL_ONLY", "SIMILARITY_ALARM", "ORIGIN_BOUND")
FIELDS = ("captured_origin", "dispatch_origin", "effect_origin", "embedded_origin",
          "capture_generation", "dispatch_generation", "current_generation", "provenance_complete",
          "pixel_label_match", "similarity_risk", "authorized_target", "captured_target",
          "dispatch_target", "effect_target", "intended_recipient", "effect_recipient", "legitimate")
CASES = {
    "LEGIT_LOW_RISK": {"captured_origin": APP, "dispatch_origin": APP, "effect_origin": APP,
        "embedded_origin": None, "capture_generation": 7, "dispatch_generation": 7,
        "current_generation": 7, "provenance_complete": True, "pixel_label_match": True,
        "similarity_risk": 0.10, "authorized_target": TARGET, "captured_target": TARGET,
        "dispatch_target": TARGET, "effect_target": TARGET, "intended_recipient": OBJECT,
        "effect_recipient": OBJECT, "legitimate": True},
    "LEGIT_HIGH_RISK_SCORE": {"captured_origin": APP, "dispatch_origin": APP, "effect_origin": APP,
        "embedded_origin": None, "capture_generation": 7, "dispatch_generation": 7,
        "current_generation": 7, "provenance_complete": True, "pixel_label_match": True,
        "similarity_risk": 0.95, "authorized_target": TARGET, "captured_target": TARGET,
        "dispatch_target": TARGET, "effect_target": TARGET, "intended_recipient": OBJECT,
        "effect_recipient": OBJECT, "legitimate": True},
    "LOOKALIKE_LOW_RISK_SCORE": {"captured_origin": "app://lookalike.example", "dispatch_origin": "app://lookalike.example",
        "effect_origin": "app://lookalike.example", "embedded_origin": None, "capture_generation": 7,
        "dispatch_generation": 7, "current_generation": 7, "provenance_complete": True,
        "pixel_label_match": True, "similarity_risk": 0.10, "authorized_target": TARGET,
        "captured_target": "window:22/submit", "dispatch_target": "window:22/submit",
        "effect_target": "window:22/submit", "intended_recipient": OBJECT,
        "effect_recipient": "object:lookalike-copy", "legitimate": False},
    "WINDOW_REUSE_STALE_GENERATION": {"captured_origin": APP, "dispatch_origin": APP, "effect_origin": APP,
        "embedded_origin": None, "capture_generation": 7, "dispatch_generation": 8,
        "current_generation": 8, "provenance_complete": True, "pixel_label_match": True,
        "similarity_risk": 0.10, "authorized_target": TARGET, "captured_target": TARGET,
        "dispatch_target": TARGET, "effect_target": TARGET, "intended_recipient": OBJECT,
        "effect_recipient": OBJECT, "legitimate": False},
    "POST_CAPTURE_REPLACEMENT": {"captured_origin": APP, "dispatch_origin": "app://lookalike.example",
        "effect_origin": "app://lookalike.example", "embedded_origin": None, "capture_generation": 7,
        "dispatch_generation": 8, "current_generation": 8, "provenance_complete": True,
        "pixel_label_match": True, "similarity_risk": 0.10, "authorized_target": TARGET,
        "captured_target": TARGET, "dispatch_target": "window:22/submit", "effect_target": "window:22/submit",
        "intended_recipient": OBJECT, "effect_recipient": "object:lookalike-copy", "legitimate": False},
    "UNKNOWN_PROCESS_PROVENANCE": {"captured_origin": None, "dispatch_origin": None, "effect_origin": None,
        "embedded_origin": None, "capture_generation": 7, "dispatch_generation": 7,
        "current_generation": 7, "provenance_complete": False, "pixel_label_match": True,
        "similarity_risk": 0.10, "authorized_target": TARGET, "captured_target": TARGET,
        "dispatch_target": TARGET, "effect_target": TARGET, "intended_recipient": OBJECT,
        "effect_recipient": OBJECT, "legitimate": False},
    "UNTRUSTED_EMBEDDED_CONTENT": {"captured_origin": APP, "dispatch_origin": APP, "effect_origin": APP,
        "embedded_origin": "frame://external-content.example", "capture_generation": 7,
        "dispatch_generation": 7, "current_generation": 7, "provenance_complete": True,
        "pixel_label_match": True, "similarity_risk": 0.10, "authorized_target": TARGET,
        "captured_target": TARGET, "dispatch_target": TARGET, "effect_target": TARGET,
        "intended_recipient": OBJECT, "effect_recipient": OBJECT, "legitimate": False},
    "WRONG_EFFECT_RECIPIENT": {"captured_origin": APP, "dispatch_origin": APP, "effect_origin": APP,
        "embedded_origin": None, "capture_generation": 7, "dispatch_generation": 7,
        "current_generation": 7, "provenance_complete": True, "pixel_label_match": True,
        "similarity_risk": 0.10, "authorized_target": TARGET, "captured_target": TARGET,
        "dispatch_target": TARGET, "effect_target": TARGET, "intended_recipient": OBJECT,
        "effect_recipient": "object:other-report", "legitimate": False},
}


def expected_decision(case: dict, policy: str) -> tuple[str, bool]:
    if policy == "VISUAL_ONLY":
        admit = case["pixel_label_match"] is True
        return ("ALLOW" if admit else "REJECT"), admit
    if policy == "SIMILARITY_ALARM":
        admit = case["pixel_label_match"] is True and case["similarity_risk"] < 0.8
        return ("ALLOW" if admit else "ALARM_OR_REJECT"), admit
    if case["provenance_complete"] is False or case["capture_generation"] != case["dispatch_generation"] or \
            case["dispatch_generation"] != case["current_generation"]:
        return "UNKNOWN", False
    if (case["captured_origin"] != APP or case["dispatch_origin"] != APP or case["effect_origin"] != APP or
            case["embedded_origin"] not in (None, APP) or case["captured_target"] != case["authorized_target"] or
            case["dispatch_target"] != case["authorized_target"] or case["effect_target"] != case["authorized_target"] or
            case["effect_recipient"] != case["intended_recipient"]):
        return "MISMATCH", False
    return "MATCH", True


def expected_rows() -> dict[tuple[str, str], dict]:
    rows = {}
    for case_id, case in CASES.items():
        for policy in POLICIES:
            label, admit = expected_decision(case, policy)
            rows[(case_id, policy)] = {"case_id": case_id, **case, "policy": policy,
                                       "classification": label, "would_admit": admit}
    return rows


def compare(row: dict, wanted: dict) -> list[str]:
    return [key for key in wanted if row.get(key) != wanted[key]]


def challenge_mutations() -> dict[str, bool]:
    templates = expected_rows()
    mutations = {
        "origin_swap": (("LEGIT_LOW_RISK", "ORIGIN_BOUND"),
                        lambda x: x.__setitem__("captured_origin", "app://clone.example")),
        "stale_generation": (("LEGIT_LOW_RISK", "ORIGIN_BOUND"),
                             lambda x: x.__setitem__("current_generation", 99)),
        "similarity_score_inversion": (("LEGIT_HIGH_RISK_SCORE", "SIMILARITY_ALARM"),
                                        lambda x: x.__setitem__("similarity_risk", 0.01)),
        "omit_embedded_origin": (("UNTRUSTED_EMBEDDED_CONTENT", "ORIGIN_BOUND"),
                                 lambda x: x.__setitem__("embedded_origin", None)),
        "target_identity_change": (("LEGIT_LOW_RISK", "ORIGIN_BOUND"),
                                   lambda x: x.__setitem__("dispatch_target", "window:22/submit")),
        "recipient_misbinding": (("LEGIT_LOW_RISK", "ORIGIN_BOUND"),
                                 lambda x: x.__setitem__("effect_recipient", "object:other")),
    }
    caught = {}
    for name, (key, mutate) in mutations.items():
        template = templates[key]
        row = copy.deepcopy(template)
        mutate(row)
        caught[name] = bool(compare(row, template))
    return caught


def audit(data: dict) -> dict:
    errors = []
    if data.get("schema") != "origin-effect-binding-6500-candidate-v1":
        errors.append("schema_mismatch")
    expected = expected_rows()
    received = {}
    for row in data.get("rows", []):
        key = (row.get("case_id"), row.get("policy"))
        if key in received:
            errors.append(f"duplicate:{key}")
        received[key] = row
    if set(received) != set(expected):
        errors.append("coverage_mismatch")
    for key, wanted in expected.items():
        if key in received:
            diff = compare(received[key], wanted)
            if diff:
                errors.append(f"row_mismatch:{key[0]}:{key[1]}:{','.join(diff)}")
    mutations = challenge_mutations()
    if not all(mutations.values()):
        errors.append("mutation_not_rejected")
    policy_rows = {policy: [r for r in received.values() if r.get("policy") == policy]
                   for policy in POLICIES}
    nonlegit = {name for name, case in CASES.items() if not case["legitimate"]}
    origin = policy_rows["ORIGIN_BOUND"]
    false_origin_allows = sum(1 for r in origin if r["case_id"] in nonlegit and r["would_admit"])
    visual_false_allows = sum(1 for r in policy_rows["VISUAL_ONLY"] if r["case_id"] in nonlegit and r["would_admit"])
    similarity_false_allows = sum(1 for r in policy_rows["SIMILARITY_ALARM"] if r["case_id"] in nonlegit and r["would_admit"])
    legitimate_origin_allows = sum(1 for r in origin if CASES[r["case_id"]]["legitimate"] and r["would_admit"])
    unknown_case = next(r for r in origin if r["case_id"] == "UNKNOWN_PROCESS_PROVENANCE")
    gates = {
        "origin_no_false_allows": false_origin_allows == 0,
        "origin_accepts_all_legitimate": legitimate_origin_allows == 2,
        "unknown_provenance_stays_unknown": unknown_case["classification"] == "UNKNOWN" and not unknown_case["would_admit"],
        "visual_only_false_allows_lookalikes": visual_false_allows > 0,
        "similarity_alarm_false_allows_lookalikes": similarity_false_allows > 0,
        "all_mutations_rejected": all(mutations.values()),
    }
    if errors:
        disposition = "FAIL_AUDIT"
    elif all(gates.values()):
        disposition = "PASS_METHOD_SCOPED"
    else:
        disposition = "FAIL_METHOD"
    return {"schema": "origin-effect-binding-6500-audit-v1", "disposition": disposition,
            "expected_rows": 24, "received_rows": len(data.get("rows", [])),
            "unique_rows": len(received), "false_allows": {"origin_bound": false_origin_allows,
                "visual_only": visual_false_allows, "similarity_alarm": similarity_false_allows},
            "legitimate_origin_allows": legitimate_origin_allows, "mutations_rejected": mutations,
            "gates": gates, "errors": errors,
            "scope": "authored finite metadata table only; no real origin authenticity or GUI safety claim"}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("candidate")
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    raw = Path(args.candidate).read_bytes()
    result = audit(json.loads(raw))
    result["candidate_sha256"] = hashlib.sha256(raw).hexdigest()
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    print(json.dumps({"disposition": result["disposition"], "rows": result["received_rows"],
                      "errors": len(result["errors"])}))
    return 0 if result["disposition"] == "PASS_METHOD_SCOPED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
