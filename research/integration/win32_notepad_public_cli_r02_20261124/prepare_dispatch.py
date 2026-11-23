"""Build the one frozen public dispatch from its retained observation."""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

TOKEN = "AI-WIN32-NOTEPAD-R02-8A41D7"


def main() -> int:
    if len(sys.argv) != 5:
        raise SystemExit(
            "usage: prepare_dispatch.py TARGET_RECEIPT OBSERVATION REPORT TARGETS_AND_PROGRAM_DIR")
    target = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    observation = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
    if (target.get("attempt_id") != "win32-notepad-public-cli-r02-20261124"
            or target.get("target_bytes_before") != 0):
        raise RuntimeError("TARGET_RECEIPT_MISMATCH")
    if (observation.get("status") != "returned"
            or observation.get("target_generation_consistency") != "matched"
            or not isinstance(observation.get("target_generation"), str)
            or len(observation["target_generation"]) != 64):
        raise RuntimeError("FRESH_OBSERVATION_NOT_ELIGIBLE")
    hwnd = target["target_window"]["hwnd"]
    if type(hwnd) is not int or hwnd <= 0:
        raise RuntimeError("INVALID_EXPLICIT_HWND")
    out_dir = Path(sys.argv[4])
    out_dir.mkdir(parents=True, exist_ok=True)
    targets = {"notepad": hwnd}
    program = {
        "schema": "agent-interface/program-v1",
        "program_id": "notepad-save-r02",
        "source": {
            "observation_seq": 1,
            "binding_revision": 1,
            "target_generations": {"notepad": observation["target_generation"]},
        },
        "authority": {
            "lease_id": "win32-notepad-r02",
            "expires_at_ns": time.monotonic_ns() + 30_000_000_000,
        },
        "terminal": {"release_all_required": True},
        "ops": [
            {"op": "focus", "target": "notepad"},
            {"op": "text", "text": TOKEN},
            {"op": "key_chord", "keys": ["CTRL", "S"]},
            {"op": "wait_update", "timeout_ms": 250},
            {"op": "release_all"},
        ],
    }
    targets_path = out_dir / "targets.json"
    program_path = out_dir / "program.json"
    if targets_path.exists() or program_path.exists():
        raise RuntimeError("DISPATCH_INPUT_ALREADY_EXISTS")
    targets_path.write_text(json.dumps(targets, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    program_path.write_text(json.dumps(program, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "schema": "agent-interface/win32-notepad-dispatch-input-r02-v1",
        "target": targets,
        "target_generation": observation["target_generation"],
        "lease_expires_at_ns": program["authority"]["expires_at_ns"],
        "program_id": program["program_id"],
        "operation_count": len(program["ops"]),
        "task_token_chars": len(TOKEN),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
