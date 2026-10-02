"""Independent raw-fixture verifier; does not import the candidate."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


ARMS = {"immediate_modal", "timing_only", "preserved_view", "preserved_view_optional_cue"}


def stable_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def expected(row: dict[str, Any]) -> dict[str, Any]:
    arm = row.get("arm")
    interrupt = row["interrupt"]
    task = row["task"]
    cue = row["cue"]
    changed = row["state"]["changed_while_interrupted"] is True
    preserve = arm in {"preserved_view", "preserved_view_optional_cue"}
    cue_visible = arm == "preserved_view_optional_cue" and cue["offer"] is True and cue["author"] == "user" and bool(cue["text"])
    urgent = interrupt["urgent_release"] is True
    if arm not in ARMS:
        raise ValueError("unknown arm")
    if urgent and interrupt["eligible_deferrable"] is not False:
        raise ValueError("urgent/deferrable contradiction")
    if task["task_id"] != row["source_view"]["task_id"]:
        raise ValueError("source task mismatch")
    if row["source_view"]["contains_hidden_content"] is not False:
        raise ValueError("private content is out of scope")
    return {
        "row_id": row["row_id"],
        "arm": arm,
        "delivery": "immediate" if urgent or arm in {"immediate_modal", "preserved_view", "preserved_view_optional_cue"} else "defer_until_user_safe_boundary",
        "urgent_not_delayed": urgent,
        "question_content_digest": interrupt["question_content_digest"],
        "answer_choices": list(task["answer_choices"]),
        "answer_facts": list(task["answer_facts"]),
        "preserved_view": row["source_view"] if preserve else None,
        "return_marker": "source_bound_view" if preserve else "underlying_task_view",
        "cue_display": {"author": "user", "text": cue["text"], "is_authority": False} if cue_visible else None,
        "state_change_warning": "revalidate_before_return_action" if changed else None,
        "return_action": "not_authorized_by_prompt_or_cue",
        "automatic_effect": False,
        "correct_action_digest": hashlib.sha256(task["independent_correct_return_action"].encode()).hexdigest(),
        "source_row_sha256": hashlib.sha256(stable_bytes(row)).hexdigest(),
    }


def audit(fixture_path: Path, candidate_path: Path) -> dict[str, Any]:
    raw = fixture_path.read_bytes()
    fixture = json.loads(raw)
    output = json.loads(candidate_path.read_bytes())
    rows = fixture.get("rows", [])
    errors = []
    ids = [row.get("row_id") for row in rows]
    if fixture.get("schema") != "human-return-resumption-fixture-v1":
        errors.append("FIXTURE_SCHEMA")
    if output.get("schema") != "human-return-resumption-candidate-v1":
        errors.append("OUTPUT_SCHEMA")
    if output.get("fixture_sha256") != hashlib.sha256(raw).hexdigest():
        errors.append("FIXTURE_HASH")
    if len(rows) != 24 or len(set(ids)) != len(ids):
        errors.append("FIXTURE_CARDINALITY_OR_IDS")
    groups: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        groups.setdefault(row.get("scenario_id"), []).append(row)
    if len(groups) != 6:
        errors.append("SCENARIO_CARDINALITY")
    for scenario, matched in groups.items():
        if {r.get("arm") for r in matched} != ARMS or len(matched) != 4:
            errors.append(f"MATCHED_ARM_COVERAGE:{scenario}")
            continue
        invariant = lambda r: (r.get("task"), r.get("interrupt"), r.get("state"), r.get("source_view"))
        if any(invariant(r) != invariant(matched[0]) for r in matched[1:]):
            errors.append(f"MATCHED_CONTENT_OR_STATE:{scenario}")
        if len({r.get("cue", {}).get("offer") for r in matched}) != 2:
            errors.append(f"CUE_OFFER_CONTRAST:{scenario}")
    if output.get("row_count") != len(rows):
        errors.append("ROW_COUNT")
    got_rows = output.get("displays")
    if not isinstance(got_rows, list) or [r.get("row_id") for r in got_rows] != ids:
        errors.append("ROW_IDENTITY_ORDER")
    if isinstance(got_rows, list) and len(got_rows) == len(rows):
        for i, (source, got) in enumerate(zip(rows, got_rows)):
            try:
                want = expected(source)
            except (KeyError, TypeError, ValueError):
                errors.append(f"INVALID_SOURCE:{i}")
                continue
            if got != want:
                errors.append(f"DISPLAY_MISMATCH:{i}")
    return {
        "schema": "human-return-resumption-audit-v1",
        "result": "PASS_METHOD_SCOPED" if not errors else "FAIL_METHOD",
        "fixture_sha256": hashlib.sha256(raw).hexdigest(),
        "rows": len(rows),
        "independently_reconstructed": len(rows) if not errors else None,
        "errors": errors,
    }


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixture", type=Path, default=Path("fixture.json"))
    parser.add_argument("--candidate", type=Path, default=Path("candidate.json"))
    parser.add_argument("--output", type=Path, default=Path("audit.json"))
    args = parser.parse_args()
    args.output.write_bytes(stable_bytes(audit(args.fixture, args.candidate)) + b"\n")
