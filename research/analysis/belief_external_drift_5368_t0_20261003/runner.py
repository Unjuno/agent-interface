"""One-shot formal candidate invocation; outputs are exclusive-create."""
from __future__ import annotations

import json
from pathlib import Path

from candidate import evaluate


def write_jsonl_exclusive(path: Path, rows: list[dict]) -> None:
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        for row in rows:
            stream.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")


def main() -> None:
    root = Path(__file__).resolve().parent
    fixture = json.loads((root / "fixture.json").read_text(encoding="utf-8"))
    candidate_rows = []
    sticky_rows = []
    age_rows = []
    for full_case in fixture["cases"]:
        public_case = {"id": full_case["id"], "input": full_case["input"]}
        candidate_rows.append(evaluate(public_case, fixture["action_contracts"]))
        safe_states = set(fixture["action_contracts"][full_case["input"]["action"]]["safe_states"])
        initial = set(full_case["input"]["initial_belief"])
        sticky_rows.append({
            "id": full_case["id"],
            "decision": "ADMIT" if initial and initial.issubset(safe_states) else "YIELD",
        })
        age_rows.append({
            "id": full_case["id"],
            "decision": "YIELD" if full_case["input"]["elapsed_steps"] > 0 else "ADMIT",
        })
    write_jsonl_exclusive(root / "formal_raw.jsonl", candidate_rows)
    write_jsonl_exclusive(root / "sticky_baseline.jsonl", sticky_rows)
    write_jsonl_exclusive(root / "age_baseline.jsonl", age_rows)


if __name__ == "__main__":
    main()
