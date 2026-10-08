#!/usr/bin/env python3
"""Finite, no-effect candidate policy comparison for Issue #6422 T0."""

import argparse
import copy
import hashlib
import json
from pathlib import Path


EFFECT_FIELDS = (
    "verb", "object", "recipient", "payload", "persistence", "side_effect"
)


def effect_signature(value):
    if not isinstance(value, dict) or set(value) != set(EFFECT_FIELDS):
        return None
    if any(not isinstance(value.get(key), str) or not value[key] for key in EFFECT_FIELDS):
        return None
    return tuple(value[key] for key in EFFECT_FIELDS)


def denial_ledger_decision(case):
    history = case.get("history")
    proposal = case.get("proposal")
    if not isinstance(history, dict) or not isinstance(proposal, dict):
        return "HOLD_EQUIVALENCE"
    if proposal.get("safety_release") is True:
        return "ALLOW_SAFETY_RELEASE"
    history_type = history.get("type")
    if history_type == "NO_RESPONSE":
        return "ASK_FRESH_APPROVAL"
    if history_type == "DEFER_UNTIL":
        condition = history.get("condition")
        evidence = proposal.get("condition_evidence")
        if (
            isinstance(condition, dict)
            and isinstance(evidence, dict)
            and evidence.get("predicate") == condition.get("predicate")
            and evidence.get("verified_by") not in (None, "agent-assertion")
            and evidence.get("valid") is True
            and isinstance(evidence.get("receipt"), str)
            and evidence["receipt"]
        ):
            return "ASK_FRESH_APPROVAL"
        return "HOLD_CONDITION_UNVERIFIED"
    if history_type != "DENY_EFFECT":
        return "HOLD_EQUIVALENCE"

    reopening = history.get("reopen_event")
    if reopening is not None:
        if (
            isinstance(reopening, dict)
            and reopening.get("initiated_by") == "user"
            and reopening.get("authenticated") is True
            and isinstance(reopening.get("event_id"), str)
            and reopening.get("event_id")
        ):
            return "ASK_FRESH_APPROVAL"
        return "HOLD_REOPEN_UNVERIFIED"

    prior_signature = effect_signature(history.get("effect"))
    proposed_signature = effect_signature(proposal.get("effect"))
    if prior_signature is None or proposed_signature is None:
        return "HOLD_EQUIVALENCE"
    if prior_signature == proposed_signature:
        return "YIELD_DENIAL"
    return "ASK_FRESH_APPROVAL"


def compare_controls(case, prior_followups):
    proposal = case.get("proposal", {})
    history = case.get("history", {})
    if proposal.get("safety_release") is True:
        return {
            "id_only": "ALLOW_SAFETY_RELEASE",
            "prompt_count_cap": "ALLOW_SAFETY_RELEASE",
        }
    original_id = history.get("request_id")
    id_only = "YIELD_DUPLICATE_ID" if original_id and proposal.get("request_id") == original_id else "ASK_FRESH_APPROVAL"
    count_cap = "YIELD_COUNT_CAP" if prior_followups >= 1 else "ASK_FRESH_APPROVAL"
    return {"id_only": id_only, "prompt_count_cap": count_cap}


def canonical_bytes(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def execute(input_path, output_path):
    input_bytes = Path(input_path).read_bytes()
    frozen = json.loads(input_bytes)
    prior_followups = frozen["prior_agent_followups_after_denial"]
    rows = []
    for case in frozen["cases"]:
        rows.append({
            "case_id": case["id"],
            "case": copy.deepcopy(case),
            "decisions": {
                "denial_ledger": denial_ledger_decision(case),
                **compare_controls(case, prior_followups),
            },
        })
    result = {
        "schema": "denial-aware-candidate-output-v1",
        "fixture_sha256": hashlib.sha256(input_bytes).hexdigest(),
        "case_count": len(rows),
        "rows": rows,
    }
    Path(output_path).write_bytes(canonical_bytes(result) + b"\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    execute(args.input, args.output)


if __name__ == "__main__":
    main()
