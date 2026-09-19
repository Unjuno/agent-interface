"""Fail-closed evaluator for the bounded #2615 scorer repair."""
from __future__ import annotations
import json
import sys
from pathlib import Path
EXPECTED_EFFECT = {"saved": True, "text": "gtk2492"}

def _stale_ok(case: dict) -> bool:
    result = case.get("adapter_result") or {}
    diagnostic = ((result.get("raw_dispatch") or {}).get("result") or {}).get("error")
    attempts = case.get("attempts") or []
    return (result.get("status") == "refused" and diagnostic == "STALE_OBSERVATION" and
            all(not a.get("consequential_input") for a in attempts) and
            all(not a.get("effect") for a in attempts))

def _task_ok(case: dict) -> bool:
    result = case.get("adapter_result") or {}
    release = result.get("release") or {}
    return (result.get("status") == "completed" and result.get("dispatch_terminal") is True and
            release.get("released") is True and release.get("cleanup_ok") is True and
            case.get("independent_effect") == EXPECTED_EFFECT and
            not case.get("provenance_contradiction", False))

def evaluate(cases: list[dict]) -> dict:
    rows = []
    for case in cases:
        kind = case["kind"]
        rows.append({"case": kind, "accepted": _stale_ok(case) if kind == "stale" else _task_ok(case)})
    expected = {"normal": True, "stale": True, "false_effect": False, "incomplete_release": False, "ambiguous_refusal": False}
    passed = (len(rows) == len(expected) and all(row["accepted"] == expected.get(row["case"], object()) for row in rows)
              and {row["case"] for row in rows} == set(expected))
    return {"schema": "golden-v3-repair-evaluation-v1", "passed": passed, "rows": rows}

def main() -> int:
    if len(sys.argv) != 3:
        print("usage: evaluator.py CASES.json RESULT.json", file=sys.stderr); return 2
    result = evaluate(json.loads(Path(sys.argv[1]).read_text(encoding="utf-8")))
    Path(sys.argv[2]).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    return 0 if result["passed"] else 1

if __name__ == "__main__":
    raise SystemExit(main())
