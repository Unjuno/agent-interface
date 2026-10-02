"""Emit only the missing immediate-modal baseline records from the frozen fixture."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


def stable_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def render(row: dict[str, Any]) -> dict[str, Any]:
    urgent = row["interrupt"]["urgent_release"] is True
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
        "urgent_release_immediate": urgent,
        "underlying_view": "overlay_without_snapshot_or_copy",
        "cue_display": None,
        "state_change_warning": "revalidate_before_return_action" if changed else None,
        "return_action_authorized": False,
        "correct_return_action_disclosed": False,
        "automatic_effect": False,
    }


def run(fixture_path: Path, output_path: Path) -> None:
    raw = fixture_path.read_bytes()
    fixture = json.loads(raw)
    rows = [row for row in fixture["rows"] if row["arm"] == "immediate_modal"]
    result = {
        "schema": "human-return-resumption-modal-candidate-v1",
        "fixture_sha256": hashlib.sha256(raw).hexdigest(),
        "row_count": len(rows),
        "rows": [render(row) for row in rows],
    }
    output_path.write_bytes(stable_bytes(result) + b"\n")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixture", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    run(args.fixture, args.output)
