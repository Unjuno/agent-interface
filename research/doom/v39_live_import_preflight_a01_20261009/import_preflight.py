#!/usr/bin/env python3
"""Import-only guard for current V39 before any app/game/model startup."""
from __future__ import annotations

import importlib
from importlib.metadata import PackageNotFoundError, version
import json
from pathlib import Path
import sys


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: import_preflight.py EXPECTED_PILLOW_VERSION", file=sys.stderr)
        return 64

    repo = Path(__file__).resolve().parents[3]
    sys.path[:0] = [str(repo / "research" / "doom"),
                    str(repo / "research" / "live_control")]
    expected_pillow = sys.argv[1]

    try:
        actual_pillow = version("Pillow")
        if actual_pillow != expected_pillow:
            raise RuntimeError(
                f"Pillow version mismatch: expected {expected_pillow}, got {actual_pillow}"
            )
        importlib.import_module("map01_overlap_controller_v39")
    except (PackageNotFoundError, ModuleNotFoundError, RuntimeError) as exc:
        print(json.dumps({
            "decision": "STOP_IMPORT_PREFLIGHT",
            "reason": type(exc).__name__,
            "detail": str(exc),
            "source_root": str(repo),
            "game_initialized": False,
            "app_server_requests": 0,
            "model_requests": 0,
            "physical_input_calls": 0,
        }, sort_keys=True))
        return 20

    print(json.dumps({
        "decision": "IMPORT_ONLY_READY",
        "pillow": actual_pillow,
        "controller_module": "map01_overlap_controller_v39",
        "controller_path": importlib.import_module(
            "map01_overlap_controller_v39").__file__,
        "python": sys.version.split()[0],
        "game_initialized": False,
        "app_server_requests": 0,
        "model_requests": 0,
        "physical_input_calls": 0,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
