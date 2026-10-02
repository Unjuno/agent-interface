"""Independent raw-fixture modal-baseline audit and six corruption controls."""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any


def stable_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def expected(row: dict[str, Any]) -> dict[str, Any]:
    changed = row["state"]["changed_while_interrupted"] is True
    return {
        "row_id": row["row_id"],
        "scenario_id": row["scenario_id"],
        "active_task_id": row["task"]["task_id"],
        "question_text": row["task"]["question_text"],
        "question_content_digest": row["interrupt"]["question_content_digest"],
        "answer_choices": list(row["task"]["answer_choices"]),
        "answer_facts": list(row["task"]["answer_facts"]),
        "delivery": "immediate",
        "urgent_release_immediate": row["interrupt"]["urgent_release"] is True,
        "underlying_view": "overlay_without_snapshot_or_copy",
        "cue_display": None,
        "state_change_warning": "revalidate_before_return_action" if changed else None,
        "return_action_authorized": False,
        "correct_return_action_disclosed": False,
        "automatic_effect": False,
    }


def validate(fixture: dict[str, Any], result: dict[str, Any], raw_hash: str) -> list[str]:
    errors = []
    source = [row for row in fixture.get("rows", []) if row.get("arm") == "immediate_modal"]
    wanted_ids = [row["row_id"] for row in source]
    rows = result.get("rows")
    if fixture.get("schema") != "human-return-resumption-fixture-v1":
        errors.append("FIXTURE_SCHEMA")
    if result.get("schema") != "human-return-resumption-modal-candidate-v1":
        errors.append("RESULT_SCHEMA")
    if result.get("fixture_sha256") != raw_hash:
        errors.append("FIXTURE_HASH")
    if len(source) != 6 or result.get("row_count") != 6:
        errors.append("MODAL_ARM_CARDINALITY")
    if not isinstance(rows, list) or [row.get("row_id") for row in rows] != wanted_ids:
        errors.append("ROW_IDENTITY_ORDER")
    if isinstance(rows, list) and len(rows) == len(source):
        for index, (raw_row, observed) in enumerate(zip(source, rows)):
            if observed != expected(raw_row):
                errors.append(f"MODAL_DISPLAY_MISMATCH:{index}")
    scenarios = {}
    for row in fixture.get("rows", []):
        scenarios.setdefault(row["scenario_id"], []).append(row)
    if len(scenarios) != 6 or any(len(group) != 4 for group in scenarios.values()):
        errors.append("MATCHED_FIXTURE_COVERAGE")
    for name, group in scenarios.items():
        invariant = lambda item: (item["task"], item["interrupt"], item["state"], item["source_view"])
        if any(invariant(item) != invariant(group[0]) for item in group[1:]):
            errors.append(f"MATCHED_FIXTURE_INVARIANT:{name}")
    return errors


def run_controls(fixture_path: Path, candidate_path: Path) -> dict[str, Any]:
    raw = fixture_path.read_bytes()
    fixture = json.loads(raw)
    original = json.loads(candidate_path.read_bytes())
    baseline_errors = validate(fixture, original, hashlib.sha256(raw).hexdigest())
    cases = {
        "changed_state_warning_removed": ("changed_external_state::immediate_modal", lambda d: d.__setitem__("state_change_warning", None)),
        "emergency_delivery_delayed": ("urgent_release::immediate_modal", lambda d: d.__setitem__("delivery", "defer_until_user_safe_boundary")),
        "question_content_changed": ("stable_cue_written::immediate_modal", lambda d: d.__setitem__("question_text", "Different question")),
        "answer_choices_changed": ("stable_cue_unused::immediate_modal", lambda d: d.__setitem__("answer_choices", ["save"])),
        "active_task_swapped": ("simple_no_cue::immediate_modal", lambda d: d.__setitem__("active_task_id", "other-task")),
        "correct_return_action_leaked": ("duplicate_effect_guard::immediate_modal", lambda d: d.__setitem__("correct_return_action_disclosed", True)),
        "automatic_effect_realized": ("simple_no_cue::immediate_modal", lambda d: d.__setitem__("automatic_effect", True)),
    }
    controls = {}
    for name, (row_id, mutate) in cases.items():
        altered = copy.deepcopy(original)
        target = next(row for row in altered["rows"] if row["row_id"] == row_id)
        mutate(target)
        rejected = bool(validate(fixture, altered, hashlib.sha256(raw).hexdigest()))
        controls[name] = {"target": row_id, "rejected": rejected}
    passed = not baseline_errors and all(control["rejected"] for control in controls.values())
    return {
        "schema": "human-return-resumption-modal-audit-v1",
        "result": "PASS_METHOD_SCOPED" if passed else "FAIL_METHOD",
        "fixture_sha256": hashlib.sha256(raw).hexdigest(),
        "audited_modal_rows": len(original.get("rows", [])),
        "baseline_errors": baseline_errors,
        "controls": controls,
        "control_count": len(controls),
        "rejected_controls": sum(value["rejected"] for value in controls.values()),
        "errors": [] if passed else [name for name, value in controls.items() if not value["rejected"]],
    }


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixture", type=Path, required=True)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.write_bytes(stable_bytes(run_controls(args.fixture, args.candidate)) + b"\n")
