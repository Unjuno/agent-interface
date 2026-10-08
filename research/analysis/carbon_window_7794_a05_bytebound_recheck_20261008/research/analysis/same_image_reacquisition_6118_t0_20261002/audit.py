#!/usr/bin/env python3
"""Independent raw-only audit; does not import candidate.py."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path


def sha(payload: str) -> str:
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def expected_route(c: dict) -> str:
    source = sha(c["source_payload"])
    if c["current_epoch"] > c["capture_epoch"]:
        if c["recapture_payload"] is None:
            return "FRESH_REACQUIRE_OR_YIELD"
        if sha(c["recapture_payload"]) == source:
            return "NEW_EPOCH_SAME_PIXELS_NO_HIDDEN_STATE_CLAIM"
        return "FRESH_EPOCH_CAPTURE_STILL_REQUIRES_EFFECT_GATE"
    if not c["trigger"]:
        return "YIELD_UNRESOLVED_TRIGGER_MISS_POSSIBLE"
    if c["pixel_adequacy"] == "inadequate":
        return "INDEPENDENT_CUE_OR_YIELD"
    b, q = c["blind_reread"], c["grounded_critique"]
    if b is not None and q is not None and b["label"] != q["label"]:
        return "YIELD_DISAGREEMENT_NO_VOTE"
    if b is not None and q is not None:
        return "ORDINARY_EXTERNAL_GATE_ONLY_REPEAT_IS_NOT_INDEPENDENT"
    return "YIELD_INCOMPLETE_REVIEW"


def expected_cost(c: dict, units: dict) -> dict:
    return {
        "first_read": units["first_read"],
        "blind_reread": units["blind_reread"] if c["trigger"] and c["blind_reread"] is not None else 0,
        "grounded_critique": units["grounded_critique"] if c["trigger"] and c["grounded_critique"] is not None else 0,
        "recapture": units["recapture"] if c["recapture_payload"] is not None else 0,
        "independent_cue": units["independent_cue"] if c["independent_cue"] is not None else 0,
    }


def audit(fixture: dict, truth_doc: dict, rows: list[dict]) -> dict:
    errors: list[str] = []
    cases = {c["case_id"]: c for c in fixture["cases"]}
    truth = truth_doc["oracle_truth"]
    ids = [r.get("case_id") for r in rows]
    expected_ids = [c["case_id"] for c in fixture["cases"]]
    if len(rows) != len(expected_ids) or len(set(ids)) != len(ids) or set(ids) != set(expected_ids):
        errors.append("case_denominator_or_uniqueness")
    by_id = {r.get("case_id"): r for r in rows}
    for case_id, c in cases.items():
        r = by_id.get(case_id)
        if r is None:
            continue
        if r.get("source_digest") != sha(c["source_payload"]):
            errors.append(f"{case_id}:source_identity")
        for field in ("capture_epoch", "current_epoch", "pixel_adequacy", "trigger", "trigger_kind",
                      "first", "blind_reread", "grounded_critique", "recapture_epoch", "independent_cue"):
            if r.get(field) != c[field]:
                errors.append(f"{case_id}:{field}")
        expected_recapture = sha(c["recapture_payload"]) if c["recapture_payload"] is not None else None
        if r.get("recapture_digest") != expected_recapture:
            errors.append(f"{case_id}:recapture_identity")
        if r.get("critique_saw_first") != (c["grounded_critique"] is not None):
            errors.append(f"{case_id}:anchoring_visibility")
        if r.get("cost_units") != expected_cost(c, fixture["cost_units"]):
            errors.append(f"{case_id}:cost_ledger")
        if r.get("recommendation") != expected_route(c):
            errors.append(f"{case_id}:recommendation")
        if r.get("action_authorized") is not False:
            errors.append(f"{case_id}:authority_firewall")

    # Independent truth-only checks for the seven frozen controls.
    checks = {
        "adequate-inferential-error": lambda c: c["first"]["label"] != truth[c["case_id"]]
            and c["blind_reread"]["label"] == truth[c["case_id"]]
            and c["grounded_critique"]["label"] == truth[c["case_id"]],
        "aliased-pixels": lambda c: c["blind_reread"]["label"] != truth[c["case_id"]]
            and c["grounded_critique"]["label"] != truth[c["case_id"]]
            and c["independent_cue"]["label"] == truth[c["case_id"]],
        "changed-world": lambda c: c["current_epoch"] > c["capture_epoch"]
            and c["first"]["label"] != truth[c["case_id"]],
        "same-bytes-new-epoch": lambda c: c["recapture_epoch"] > c["capture_epoch"]
            and sha(c["recapture_payload"]) == sha(c["source_payload"])
            and truth[c["case_id"]] == "UNKNOWN",
        "high-confidence-trigger-miss": lambda c: not c["trigger"]
            and float(c["first"]["confidence"]) >= 0.9
            and c["first"]["label"] != truth[c["case_id"]],
        "answer-anchoring": lambda c: c["blind_reread"]["label"] == truth[c["case_id"]]
            and c["grounded_critique"]["label"] != truth[c["case_id"]],
        "no-error-overhead": lambda c: c["trigger"]
            and c["first"]["label"] == truth[c["case_id"]]
            and c["blind_reread"]["label"] == c["first"]["label"]
            and c["grounded_critique"]["label"] == c["first"]["label"],
    }
    for case_id, check in checks.items():
        if case_id not in cases or not check(cases[case_id]):
            errors.append(f"truth_control:{case_id}")
    for case_id, r in by_id.items():
        if case_id in cases and r.get("action_authorized") is not False:
            errors.append("truth_seen_as_authority")
    return {
        "schema": "same-image-reacquisition-6118-t0-audit-v1",
        "disposition": "PASS_METHOD_SCOPED" if not errors else "FAIL_METHOD_SCOPED",
        "case_count": len(rows),
        "case_ids": ids,
        "errors": errors,
        "limitations": ["authored no-model ledger", "synthetic source tokens, not images",
                        "cost units are not wall time or model tokens", "no action/effect authority"],
    }


def main(argv: list[str]) -> int:
    if len(argv) != 5:
        print("usage: audit.py FIXTURE TRUTH RAW OUTPUT", file=sys.stderr)
        return 2
    fixture = json.loads(Path(argv[1]).read_text(encoding="utf-8"))
    truth_doc = json.loads(Path(argv[2]).read_text(encoding="utf-8"))
    rows = [json.loads(line) for line in Path(argv[3]).read_text(encoding="utf-8").splitlines() if line]
    result = audit(fixture, truth_doc, rows)
    Path(argv[4]).write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    return 0 if result["disposition"] == "PASS_METHOD_SCOPED" else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
