#!/usr/bin/env python3
"""Import-only R1 gate for the MAP01 v12 namespace repair.

This script deliberately performs no GUI, model, X11, network, or ViZDoom call.
It imports the retained live_control stack only after making its directory the
sole provider of the legacy bare module names.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import py_compile
import sys
from pathlib import Path


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    repo = args.repo.resolve()
    live = repo / "research" / "live_control"
    retained = [
        repo / "research" / "doom" / "session_v7.py",
        live / "session_v8.py",
        live / "session_v7.py",
        live / "session_v6.py",
    ]
    if not all(p.is_file() for p in retained):
        raise SystemExit("retained source missing")
    args.out.mkdir(parents=True, exist_ok=False)

    for p in sorted(live.glob("*.py")):
        py_compile.compile(str(p), doraise=True)

    expected = {str(p.relative_to(repo)): sha256(p) for p in retained}
    sys.path = [str(live)] + [
        p for p in sys.path if Path(p or ".").resolve() not in {live, repo / "research" / "doom"}
    ]
    for name in ("session_v8", "session_v7", "session_v6", "session_v5",
                 "session_v4", "executor_v3", "lease", "input_owner_v2"):
        sys.modules.pop(name, None)
    importlib.invalidate_caches()
    v8 = importlib.import_module("session_v8")
    v7 = importlib.import_module("session_v7")

    checks = {
        "backend_symbol": v8.Backend.__name__ == "Backend",
        "backend_module": v8.Backend.__module__ == "session_v8",
        "previous_module": v7.Backend.__module__ == "session_v7",
        "suite_symbol": hasattr(v8, "suite"),
        "no_doom_entrypoint_loaded": "session_v7.py" not in str(getattr(sys.modules["session_v7"], "__file__", "")),
    }
    result = {
        "disposition": "PASS_MAP01_R1_IMPORT_GRAPH_REPAIR_SCOPED"
        if all(checks.values()) else "FAIL_MAP01_R1_IMPORT_GRAPH_REPAIR_SCOPED",
        "checks": checks,
        "source_sha256": expected,
        "imported": {
            "session_v8": str(Path(v8.__file__).resolve()),
            "session_v7": str(Path(v7.__file__).resolve()),
        },
        "scope": "import readiness only; no GUI/model/X11/network/formal session",
    }
    (args.out / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    if not all(checks.values()):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
