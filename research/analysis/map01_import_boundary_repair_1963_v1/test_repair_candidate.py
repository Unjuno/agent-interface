"""Compile-only candidate for an explicit live-control import boundary."""
from __future__ import annotations

import ast
import json
import tempfile
from pathlib import Path

ROOT = Path(__file__).parents[3]
LIVE = ROOT / "research/live_control"


def main() -> int:
    source = (LIVE / "session_v8.py").read_text(encoding="utf-8")
    tree = ast.parse(source, filename="session_v8.py")
    changed = 0
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.level == 0 and node.module == "session_v7":
            node.module = "agent_live_control_session_v7"
            changed += 1
    if changed != 1:
        raise AssertionError(f"expected exactly one ambiguous import, got {changed}")
    candidate = ast.unparse(tree) + "\n"
    with tempfile.TemporaryDirectory(prefix="map01-import-boundary-") as tmp:
        out = Path(tmp)
        (out / "session_v8_candidate.py").write_text(candidate, encoding="utf-8")
        # Compile only. Importing the historical GUI stack would violate this
        # successor's source-only gate and would not prove module resolution.
        compile(candidate, str(out / "session_v8_candidate.py"), "exec")
    result = {
        "decision": "PASS_IMPORT_BOUNDARY_CANDIDATE_COMPILE_SCOPED",
        "ambiguous_imports_rewritten": changed,
        "shared_runtime_modified": False,
        "x11_calls": 0,
        "input_calls": 0,
        "model_calls": 0,
        "formal_invocations": 0,
    }
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
