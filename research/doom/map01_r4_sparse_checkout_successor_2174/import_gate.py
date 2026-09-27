"""Source-only MAP01 import-boundary check for successor #2174."""
from __future__ import annotations
import ast, json, py_compile, sys
from pathlib import Path
root = Path(__file__).resolve().parents[3]
target = root / "research/doom/map01_v12_physical_occupancy_live_r1_v1/session_entry.py"
try:
    tree = ast.parse(target.read_text(encoding="utf-8"), filename=str(target))
    py_compile.compile(str(target), doraise=True)
    forbidden = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            name = node.func.attr if isinstance(node.func, ast.Attribute) else node.func.id if isinstance(node.func, ast.Name) else ""
            if name in {"main", "DoomGame", "subprocess", "construction", "formal"}:
                forbidden.append(name)
    result = {"status": "PASS_GATE_REACHED_NO_SCIENCE" if not forbidden else "STOP_FORBIDDEN_LAUNCHER_SIDE_EFFECT", "forbidden_calls": forbidden, "construction": 0, "formal": 0, "input": 0, "model": 0}
except Exception as exc:
    result = {"status": "STOP_GATE_EXCEPTION", "error_type": type(exc).__name__, "error": str(exc), "construction": 0, "formal": 0, "input": 0, "model": 0}
print(json.dumps(result, sort_keys=True))
if result["status"] != "PASS_GATE_REACHED_NO_SCIENCE":
    sys.exit(1)
