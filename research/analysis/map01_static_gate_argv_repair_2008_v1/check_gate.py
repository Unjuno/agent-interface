"""Source-only argv contract check for Issue #2008."""
from __future__ import annotations

import ast
import json
from pathlib import Path

ROOT = Path(__file__).parents[3]
TARGET = ROOT / "research/doom/session_map01_v13.py"


def main() -> int:
    tree = ast.parse(TARGET.read_text(encoding="utf-8"), filename=str(TARGET))
    required = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "_option" and node.args:
            if isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str):
                if node.args[0].value not in required:
                    required.append(node.args[0].value)
    expected = ["--out"]
    result = {
        "decision": "PASS_STATIC_GATE_ARGV_CONTRACT_SCOPED",
        "required_options": required,
        "expected_required_options": expected,
        "temporary_output_path": "work/map01-r1-argv-repair/gate",
        "construction_invocations": 0,
        "formal_invocations": 0,
        "input_calls": 0,
        "model_calls": 0,
        "x11_calls": 0,
    }
    if "--out" not in required:
        result["decision"] = "FAIL_STATIC_GATE_ARGV_CONTRACT"
        print(json.dumps(result, sort_keys=True))
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
