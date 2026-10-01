"""Independent pre-fit check for Issue #4205's frozen support allocation."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def canonical(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def main() -> int:
    freeze = json.loads((ROOT / "TRAINING_FREEZE.json").read_text(encoding="utf-8"))
    cases = json.loads((ROOT / "base" / "CASES.json").read_text(encoding="utf-8"))
    examples = [json.loads(line) for line in (ROOT / "support-32.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    errors: list[str] = []

    for name, expected in freeze["source_sha256"].items():
        path = ROOT / name
        if not path.is_file() or sha256(path) != expected:
            errors.append("source_hash:" + name)
    if len(examples) != 32 or freeze["support_set"]["rows"] != 32:
        errors.append("row_count")
    if len({row.get("query") for row in examples}) != 32:
        errors.append("duplicate_query")
    eval_tasks = {case["task"] for case in cases["cases"]}
    eval_states = {canonical(case["state"]) for case in cases["cases"]}
    tools = cases["tools"]
    counts: dict[str, int] = {}
    for row in examples:
        if row.get("system") != "device: isolated desktop-settings simulator; network: disabled":
            errors.append("system_mismatch")
        if row.get("tools") != tools:
            errors.append("tool_schema_mismatch")
        if any(key in row for key in ("reasoning", "chain_of_thought", "cot")):
            errors.append("reasoning_field_present")
        query = row.get("query", "")
        task = query.partition("Task: ")[2].partition("\nCurrent visible simulator state")[0]
        state_text = query.partition("Current visible simulator state (JSON): ")[2].partition("\nPolicy:")[0]
        if task in eval_tasks:
            errors.append("heldout_task_overlap")
        try:
            state = json.loads(state_text)
            if canonical(state) in eval_states:
                errors.append("heldout_state_overlap")
        except json.JSONDecodeError:
            errors.append("invalid_state_json")
        answers = row.get("answers")
        if not isinstance(answers, list) or len(answers) != 1 or not isinstance(answers[0], dict):
            errors.append("not_one_next_action")
        else:
            name = answers[0].get("name")
            counts[name] = counts.get(name, 0) + 1

    expected_counts = {"SET_FIELD": 10, "CLICK": 14, "YIELD": 5, "NO_ACTION": 3}
    if counts != expected_counts:
        errors.append("label_composition")
    result = {
        "schema": "cactus-needle3-support-freeze-audit-v1",
        "pass": not errors,
        "errors": errors,
        "rows": len(examples),
        "sha256": sha256(ROOT / "support-32.jsonl"),
        "labels": counts,
        "heldout_task_or_state_overlap": any("heldout_" in error for error in errors),
        "hidden_reasoning_fields": any("reasoning" in error for error in errors),
    }
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2))
    return 0 if not errors else 2


if __name__ == "__main__":
    raise SystemExit(main())

