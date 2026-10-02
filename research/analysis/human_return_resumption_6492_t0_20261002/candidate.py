"""Deterministic presentation-contract candidate; no people or applications."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


def stable_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def render(row: dict[str, Any]) -> dict[str, Any]:
    arm = row["arm"]
    urgent = row["interrupt"]["urgent_release"] is True
    preserve = arm in {"preserved_view", "preserved_view_optional_cue"}
    cue = row["cue"]
    cue_visible = (
        arm == "preserved_view_optional_cue"
        and cue["offer"] is True
        and cue["author"] == "user"
        and bool(cue["text"])
    )
    changed = row["state"]["changed_while_interrupted"] is True
    return {
        "row_id": row["row_id"],
        "arm": arm,
        "delivery": "immediate" if urgent or arm == "immediate_modal" else "defer_until_user_safe_boundary" if arm == "timing_only" else "immediate",
        "urgent_not_delayed": urgent,
        "question_content_digest": row["interrupt"]["question_content_digest"],
        "answer_choices": list(row["task"]["answer_choices"]),
        "answer_facts": list(row["task"]["answer_facts"]),
        "preserved_view": row["source_view"] if preserve else None,
        "return_marker": "source_bound_view" if preserve else "underlying_task_view",
        "cue_display": {"author": "user", "text": cue["text"], "is_authority": False} if cue_visible else None,
        "state_change_warning": "revalidate_before_return_action" if changed else None,
        "return_action": "not_authorized_by_prompt_or_cue",
        "automatic_effect": False,
        "correct_action_digest": hashlib.sha256(row["task"]["independent_correct_return_action"].encode()).hexdigest(),
        "source_row_sha256": hashlib.sha256(stable_bytes(row)).hexdigest(),
    }


def run(fixture_path: Path, output_path: Path) -> None:
    raw = fixture_path.read_bytes()
    fixture = json.loads(raw)
    displays = [render(row) for row in fixture["rows"]]
    output = {
        "schema": "human-return-resumption-candidate-v1",
        "fixture_sha256": hashlib.sha256(raw).hexdigest(),
        "row_count": len(displays),
        "displays": displays,
    }
    output_path.write_bytes(stable_bytes(output) + b"\n")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixture", type=Path, default=Path("fixture.json"))
    parser.add_argument("--output", type=Path, default=Path("candidate.json"))
    args = parser.parse_args()
    run(args.fixture, args.output)
