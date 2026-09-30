#!/usr/bin/env python3
"""Independent raw-output auditor; intentionally imports no simulator code."""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path


PATTERNS = {"clean_commit", "read_then_abort", "delayed_completion", "mixed_generation",
            "supersession", "rollback_after_read", "duplicate_completion", "tentative_presentation"}
ROLES = {"action_consumed", "presentation_only"}


def oracle(events: list[dict]) -> dict:
    """Reconstruct action validity from raw chronological events only."""
    seqs = [e.get("seq") for e in events]
    if any(not isinstance(s, int) for s in seqs) or seqs != sorted(set(seqs)):
        raise ValueError("event_sequence_not_strict")
    reads = [e for e in events if e.get("type") == "read" and e.get("id") == "r1"]
    if len(reads) != 1:
        raise ValueError("read_event_cardinality")
    read = reads[0]
    uses = [e for e in events if e.get("type") in {"consume", "present_only"}
            and e.get("read_id") == "r1"]
    if len(uses) != 1:
        raise ValueError("read_use_cardinality")
    use = uses[0]
    state = "tentative"
    generation = read.get("generation")
    status_at_use = None
    generation_at_use = None
    for event in events:
        kind = event.get("type")
        if kind in {"commit", "abort", "rollback"}:
            state = {"commit": "committed", "abort": "aborted",
                     "rollback": "rolled_back"}[kind]
        elif kind == "supersede":
            if event.get("old_generation") != generation or event.get("new_generation") <= generation:
                raise ValueError("invalid_supersession")
            generation = event["new_generation"]
        if event is use:
            status_at_use = state
            generation_at_use = generation
    action = use.get("type") == "consume"
    reason = None
    if action:
        before = [e for e in events if e["seq"] < use["seq"]]
        after = [e for e in events if e["seq"] > use["seq"]]
        if any(e.get("type") == "abort" for e in before):
            reason = "aborted_before_consume"
        elif any(e.get("type") == "rollback" for e in before):
            reason = "rolled_back_before_consume"
        elif status_at_use != "committed":
            reason = "not_committed_at_consume"
        elif any(e.get("type") == "abort" for e in after):
            reason = "aborted_after_consume"
        elif any(e.get("type") == "rollback" for e in after):
            reason = "rolled_back_after_consume"
        elif read.get("generation") != use.get("action_epoch") or generation_at_use != read.get("generation"):
            reason = "generation_mismatch"
    return {
        "action_attempted": action,
        "action_epoch": use.get("action_epoch"),
        "final_generation": generation,
        "oracle_invalid_reason": reason,
        "read_provenance": {
            "read_id": read["id"], "source_generation": read.get("generation"),
            "producer_final_status": state, "consume_seq": use["seq"],
            "action_relevant": action, "consumer_action": use.get("action_id"),
        },
    }


def check_rows(data: dict) -> list[str]:
    errors = []
    rows = data.get("rows")
    if data.get("schema") != "opacity-action-relevance-5360-t1/v1" or not isinstance(rows, list):
        return ["schema_or_rows_invalid"]
    keys = {(r.get("pattern"), r.get("role"), r.get("policy")) for r in rows}
    expected = {(p, role, policy) for p in PATTERNS for role in ROLES
                for policy in {"FINAL_STATE_ONLY", "ACTION_RELEVANT_OPACITY"}}
    if len(rows) != 32 or keys != expected:
        errors.append("matrix_not_exact_32")
    grouped = {}
    for row in rows:
        key = (row.get("pattern"), row.get("role"))
        grouped.setdefault(key, {})[row.get("policy")] = row
        try:
            derived = oracle(row.get("events", []))
        except (ValueError, TypeError, KeyError):
            errors.append(f"history_structure_invalid:{key}")
            continue
        for field, value in derived.items():
            if row.get(field) != value:
                errors.append(f"history_projection_mismatch:{key}:{field}")
        if row.get("role") != ("action_consumed" if derived["action_attempted"] else "presentation_only"):
            errors.append(f"action_role_event_mismatch:{key}")
        reason = derived["oracle_invalid_reason"]
        strict = row["decision"]
        if row["policy"] == "ACTION_RELEVANT_OPACITY":
            expected_accept = reason is None and derived["action_attempted"]
            if strict["accepted"] != expected_accept:
                errors.append(f"strict_decision_mismatch:{key}")
            expected_first = None if reason is None else "r1"
            if strict["first_invalid_read"] != expected_first:
                errors.append(f"first_invalid_read_missing:{key}")
    witnesses = 0
    for key, pair in grouped.items():
        a, b = pair["FINAL_STATE_ONLY"], pair["ACTION_RELEVANT_OPACITY"]
        if oracle(a["events"])["oracle_invalid_reason"] and a["decision"]["accepted"] and not b["decision"]["accepted"]:
            witnesses += 1
    if witnesses == 0:
        errors.append("HOLD_NO_DISCRIMINATOR")

    return sorted(set(errors))


def check(data: dict) -> list[str]:
    errors = check_rows(data)
    if errors:
        return errors

    # Mutation controls must be detected by the independent oracle/structural checks.
    rows = data["rows"]
    control = next(r for r in rows if r["pattern"] == "read_then_abort" and r["role"] == "action_consumed"
                   and r["policy"] == "ACTION_RELEVANT_OPACITY")
    def mutation_rejected(original: dict, altered: dict, expected_error: str) -> bool:
        changed = copy.deepcopy(data)
        for index, candidate in enumerate(changed["rows"]):
            if (candidate["pattern"], candidate["role"], candidate["policy"]) == (
                    original["pattern"], original["role"], original["policy"]):
                changed["rows"][index] = altered
                break
        return any(error.startswith(expected_error + ":") for error in check_rows(changed))

    mutated = copy.deepcopy(control)
    next(e for e in mutated["events"] if e["type"] == "abort")["type"] = "commit"
    if not mutation_rejected(control, mutated, "history_projection_mismatch"):
        errors.append("mutation_abort_to_commit_not_detected")
    mutated = copy.deepcopy(control)
    next(e for e in mutated["events"] if e["type"] == "consume")["type"] = "present_only"
    if not mutation_rejected(control, mutated, "action_role_event_mismatch"):
        errors.append("mutation_action_relevance_not_detected")
    generation_control = next(r for r in rows if r["pattern"] == "mixed_generation"
                              and r["role"] == "action_consumed"
                              and r["policy"] == "ACTION_RELEVANT_OPACITY")
    mutated = copy.deepcopy(generation_control)
    next(e for e in mutated["events"] if e["type"] == "consume")["action_epoch"] = 1
    if not mutation_rejected(generation_control, mutated, "history_projection_mismatch"):
        errors.append("mutation_generation_not_detected")
    return sorted(set(errors))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("raw", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = {"audit": "PASS_T1_SCOPED" if not check(json.loads(args.raw.read_text(encoding="utf-8"))) else "FAIL",
              "errors": check(json.loads(args.raw.read_text(encoding="utf-8")))}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    if args.output.exists():
        raise SystemExit(f"refusing to overwrite audit output: {args.output}")
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    if result["errors"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
