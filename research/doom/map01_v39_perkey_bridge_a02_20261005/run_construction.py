#!/usr/bin/env python3
"""Run the frozen V4/V12 fake-display composition once."""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
OUT = HERE / "results/construction-a02"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def stop(reason: str) -> int:
    path = HERE / "results/preflight-stop-a02/STOP.json"
    path.parent.mkdir(parents=True, exist_ok=False)
    path.write_text(json.dumps({
        "run_id": "MAP01-V39-PERKEY-BRIDGE-CONSTRUCTION-A02-20261005",
        "status": "STOP_BEFORE_CANDIDATE",
        "reason": reason,
    }, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "STOP_BEFORE_CANDIDATE", "reason": reason}))
    return 2


def main() -> int:
    freeze = json.loads((HERE / "FREEZE.json").read_text(encoding="utf-8"))
    current_commit = subprocess.run(
        ["git", "-C", str(REPO), "rev-parse", "HEAD"],
        check=True, capture_output=True, text=True,
    ).stdout.strip()
    if current_commit != freeze["base_commit"]:
        return stop("base_commit_mismatch")
    for relative, expected in freeze["source_sha256"].items():
        path = REPO / relative
        if not path.is_file() or sha(path.read_bytes()) != expected:
            return stop("source_sha256:" + relative)

    OUT.mkdir(parents=True, exist_ok=False)
    sys.path.insert(0, str(REPO / "research" / "doom"))
    from map01_v39_perkey_bridge_a02_20261005.composition import run_composition

    candidate = run_composition()
    event_bytes = b"".join(
        (json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
        for row in candidate["events"]
    )
    operation_bytes = b"".join(
        (json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
        for row in candidate["operations"]
    )
    (OUT / "candidate-events.jsonl").write_bytes(event_bytes)
    (OUT / "operation-trace.jsonl").write_bytes(operation_bytes)
    releases = [row for row in candidate["events"]
                if row.get("event") == "input_release_transition"]
    release_gap_ns = None
    if len(releases) == 2:
        release_gap_ns = (
            releases[1]["release_call_started_ns"]
            - releases[0]["release_call_returned_ns"]
        )
    result = {
        "schema": "map01-v39-v4-v12-composition-candidate-v1",
        "run_id": freeze["run_id"],
        "base_commit": current_commit,
        "status": "CANDIDATE_EXECUTED",
        "environment": {
            "fake_x_display": True,
            "os_input": False,
            "gui_capture": False,
            "vizdoom": False,
            "model_calls": 0,
            "docker": False,
        },
        "candidate": {
            "events_sha256": sha(event_bytes),
            "operation_trace_sha256": sha(operation_bytes),
            "event_count": len(candidate["events"]),
            "operation_count": len(candidate["operations"]),
            "fake_display_counts": candidate["fake_display_counts"],
            "physical_keys_after": candidate["physical_keys_after"],
            "backend_held_after": candidate["backend_held_after"],
            "inter_release_call_gap_ns": release_gap_ns,
        },
        "scope": (
            "actual V4 backend execute/raw methods, the retained V12 transition "
            "adapter, and the V12 fake X display only; no production startup, live "
            "X11, GUI, OS input, game, model, or latency qualification"
        ),
    }
    (OUT / "candidate.json").write_text(
        json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({"status": result["status"], "event_count": len(candidate["events"]),
                      "inter_release_call_gap_ns": release_gap_ns}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
