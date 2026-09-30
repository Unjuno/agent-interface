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


def oracle(row: dict) -> str | None:
    if row["role"] != "action_consumed":
        return None
    p = row["pattern"]
    if p in {"read_then_abort", "rollback_after_read"}:
        return "aborted" if p == "read_then_abort" else "rolled_back"
    if p == "delayed_completion":
        return "not_committed_at_consume"
    if row["read_provenance"]["source_generation"] != row["action_epoch"]:
        return "generation_mismatch"
    if p == "tentative_presentation":
        return "not_committed_at_consume"
    return None


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
        key = (row["pattern"], row["role"])
        grouped.setdefault(key, {})[row["policy"]] = row
        reason = oracle(row)
        if reason != row.get("oracle_invalid_reason"):
            errors.append(f"independent_oracle_mismatch:{key}")
        if row["read_provenance"]["action_relevant"] != (row["role"] == "action_consumed"):
            errors.append(f"action_relevance_provenance_mismatch:{key}")
        if row["role"] == "presentation_only":
            if row["action_attempted"] or row["read_provenance"]["action_relevant"]:
                errors.append(f"presentation_caused_action:{key}")
        strict = row["decision"]
        if row["policy"] == "ACTION_RELEVANT_OPACITY":
            expected_accept = reason is None and row["action_attempted"]
            if strict["accepted"] != expected_accept:
                errors.append(f"strict_decision_mismatch:{key}")
            expected_first = None if reason is None else "r1"
            if strict["first_invalid_read"] != expected_first:
                errors.append(f"first_invalid_read_missing:{key}")
    witnesses = 0
    for key, pair in grouped.items():
        a, b = pair["FINAL_STATE_ONLY"], pair["ACTION_RELEVANT_OPACITY"]
        if oracle(a) and a["decision"]["accepted"] and not b["decision"]["accepted"]:
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
    mutated["oracle_invalid_reason"] = None
    if not mutation_rejected(control, mutated, "independent_oracle_mismatch"):
        errors.append("mutation_abort_to_commit_not_detected")
    mutated = copy.deepcopy(control)
    mutated["read_provenance"]["action_relevant"] = False
    if not mutation_rejected(control, mutated, "action_relevance_provenance_mismatch"):
        errors.append("mutation_action_relevance_not_detected")
    generation_control = next(r for r in rows if r["pattern"] == "mixed_generation"
                              and r["role"] == "action_consumed"
                              and r["policy"] == "ACTION_RELEVANT_OPACITY")
    mutated = copy.deepcopy(generation_control)
    mutated["read_provenance"]["source_generation"] = mutated["action_epoch"]
    if not mutation_rejected(generation_control, mutated, "independent_oracle_mismatch"):
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
