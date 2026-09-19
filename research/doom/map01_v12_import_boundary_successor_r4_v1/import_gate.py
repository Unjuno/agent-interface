"""Side-effect-free MAP01 import-boundary gate.

This gate is intentionally source-only: it compiles selected modules and checks
that the launcher is never called. It does not import the scientific launcher,
open X11/ViZDoom, or allocate construction/formal work.
"""
from __future__ import annotations

import ast
import json
import py_compile
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
TARGET = ROOT / "research/doom/map01_v12_physical_occupancy_live_r1_v1/session_entry.py"
FORBIDDEN = {"main", "construction", "formal", "DoomGame", "XTest", "subprocess"}

tree = ast.parse(TARGET.read_text(encoding="utf-8"), filename=str(TARGET))
calls = []
for node in ast.walk(tree):
    if isinstance(node, ast.Call):
        name = node.func.attr if isinstance(node.func, ast.Attribute) else node.func.id if isinstance(node.func, ast.Name) else ""
        if name in FORBIDDEN:
            calls.append(name)
py_compile.compile(str(TARGET), doraise=True)
result = {
    "status": "PASS_MAP01_R4_SIDE_EFFECT_FREE_IMPORT_GATE_SCOPED" if not calls else "STOP_MAP01_R4_FORBIDDEN_SIDE_EFFECT",
    "target": str(TARGET.relative_to(ROOT)),
    "forbidden_calls": calls,
    "science_counters": {"construction": 0, "formal": 0, "input": 0, "model": 0, "network": 0},
}
print(json.dumps(result, sort_keys=True))
if calls:
    sys.exit(1)
