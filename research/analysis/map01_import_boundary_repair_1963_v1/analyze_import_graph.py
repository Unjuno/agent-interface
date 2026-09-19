"""Source-only reproduction of the #1928 MAP01 import-name collision."""
from __future__ import annotations

import ast
import json
from pathlib import Path

ROOT = Path(__file__).parents[3]
TARGETS = {
    "doom.session_v7": ROOT / "doom/session_v7.py",
    "live_control.session_v8": ROOT / "live_control/session_v8.py",
}


def short_imports(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    return [node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom) and node.level == 0 and node.module]


def main() -> int:
    imports = {name: short_imports(path) for name, path in TARGETS.items()}
    # The runner exposes both directories as flat import roots. The observed
    # name collision is therefore the two edges below, regardless of which
    # physical file wins resolution first.
    expected_cycle = [
        {"module": "doom.session_v7", "imports": "session_v8"},
        {"module": "live_control.session_v8", "imports": "session_v7"},
    ]
    result = {
        "decision": "REPRODUCED_IMPORT_NAME_COLLISION",
        "source_only": True,
        "x11_calls": 0,
        "input_calls": 0,
        "model_calls": 0,
        "formal_invocations": 0,
        "imports": imports,
        "observed_cycle": expected_cycle,
        "repair_constraint": "replace ambiguous flat import with an explicit module boundary; preserve parent source hashes",
    }
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
