#!/usr/bin/env python3
"""Serialize the frozen no-model visible ledger; oracle truth is not read."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path


def digest(payload: str) -> str:
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def recommendation(case: dict) -> str:
    if case["current_epoch"] > case["capture_epoch"]:
        if case["recapture_payload"] is None:
            return "FRESH_REACQUIRE_OR_YIELD"
        if digest(case["recapture_payload"]) == digest(case["source_payload"]):
            return "NEW_EPOCH_SAME_PIXELS_NO_HIDDEN_STATE_CLAIM"
        return "FRESH_EPOCH_CAPTURE_STILL_REQUIRES_EFFECT_GATE"
    if not case["trigger"]:
        return "YIELD_UNRESOLVED_TRIGGER_MISS_POSSIBLE"
    blind = case["blind_reread"]
    critique = case["grounded_critique"]
    if case["pixel_adequacy"] == "inadequate":
        return "INDEPENDENT_CUE_OR_YIELD"
    if blind is not None and critique is not None and blind["label"] != critique["label"]:
        return "YIELD_DISAGREEMENT_NO_VOTE"
    if blind is not None and critique is not None:
        return "ORDINARY_EXTERNAL_GATE_ONLY_REPEAT_IS_NOT_INDEPENDENT"
    return "YIELD_INCOMPLETE_REVIEW"


def build_rows(fixture: dict) -> list[dict]:
    unit = fixture["cost_units"]
    result = []
    for case in fixture["cases"]:
        cost = {"first_read": unit["first_read"], "blind_reread": 0,
                "grounded_critique": 0, "recapture": 0, "independent_cue": 0}
        if case["trigger"] and case["blind_reread"] is not None:
            cost["blind_reread"] = unit["blind_reread"]
        if case["trigger"] and case["grounded_critique"] is not None:
            cost["grounded_critique"] = unit["grounded_critique"]
        if case["recapture_payload"] is not None:
            cost["recapture"] = unit["recapture"]
        if case["independent_cue"] is not None:
            cost["independent_cue"] = unit["independent_cue"]
        row = {
            "case_id": case["case_id"],
            "source_digest": digest(case["source_payload"]),
            "capture_epoch": case["capture_epoch"],
            "current_epoch": case["current_epoch"],
            "pixel_adequacy": case["pixel_adequacy"],
            "trigger": case["trigger"],
            "trigger_kind": case["trigger_kind"],
            "first": case["first"],
            "blind_reread": case["blind_reread"],
            "grounded_critique": case["grounded_critique"],
            "critique_saw_first": case["grounded_critique"] is not None,
            "recapture_digest": (digest(case["recapture_payload"])
                                 if case["recapture_payload"] is not None else None),
            "recapture_epoch": case["recapture_epoch"],
            "independent_cue": case["independent_cue"],
            "cost_units": cost,
            "recommendation": recommendation(case),
            "action_authorized": False,
        }
        result.append(row)
    return result


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        print("usage: candidate.py FIXTURE OUTPUT", file=sys.stderr)
        return 2
    fixture = json.loads(Path(argv[1]).read_text(encoding="utf-8"))
    output = Path(argv[2])
    with output.open("w", encoding="utf-8", newline="\n") as stream:
        for row in build_rows(fixture):
            stream.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
