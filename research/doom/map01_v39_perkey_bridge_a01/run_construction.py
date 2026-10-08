#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
WORKTREE = HERE.parents[2]
BASELINE = WORKTREE / "research/doom/results/map01-v39-coast-liveness-live-01/runtime/events.jsonl"
FREEZE = HERE / "FREEZE.json"
OUT = HERE / "results/construction-a01"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def verify_sources(freeze: dict) -> None:
    for relative, expected in freeze["source_sha256"].items():
        path = WORKTREE / relative
        if not path.is_file() or sha(path.read_bytes()) != expected:
            raise RuntimeError("STOP_SOURCE_HASH:" + relative)


def main() -> int:
    if OUT.exists():
        raise SystemExit("STOP_OUTPUT_EXISTS:" + str(OUT))
    freeze = json.loads(FREEZE.read_text(encoding="utf-8"))
    verify_sources(freeze)
    if subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=WORKTREE, text=True).strip() != freeze["base_commit"]:
        raise SystemExit("STOP_BASE_COMMIT")
    baseline_bytes = BASELINE.read_bytes()
    if sha(baseline_bytes) != freeze["source_sha256"][BASELINE.relative_to(WORKTREE).as_posix()]:
        raise SystemExit("STOP_BASELINE_HASH")

    started_ns = time.perf_counter_ns()
    sys.path.insert(0, str(HERE))
    from test_bridge import run_bridge
    candidate = run_bridge()
    finished_ns = time.perf_counter_ns()

    baseline_rows = [json.loads(line) for line in baseline_bytes.splitlines() if line]
    baseline_per_key = [row for row in baseline_rows
                        if row.get("event") == "input_release_transition"]
    OUT.mkdir(parents=True, exist_ok=False)
    raw = b"".join((json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
                   for row in candidate["events"])
    (OUT / "candidate-events.jsonl").write_bytes(raw)
    result = {
        "schema": "map01-v39-perkey-bridge-construction-result-v1",
        "run_id": freeze["run_id"],
        "status": "CANDIDATE_EXECUTED",
        "base_commit": freeze["base_commit"],
        "host": sys.platform,
        "python": sys.version,
        "started_monotonic_ns": started_ns,
        "finished_monotonic_ns": finished_ns,
        "baseline_v39": {
            "events_sha256": sha(baseline_bytes),
            "event_count": len(baseline_rows),
            "input_release_transition_count": len(baseline_per_key),
        },
        "candidate": {
            "events_file": "candidate-events.jsonl",
            "events_sha256": sha(raw),
            "event_count": len(candidate["events"]),
            "fake_physical_keys_after_up": candidate["fake_physical_keys_after_up"],
            "backend_held_after_up": candidate["backend_held_after_up"],
        },
        "environment": {
            "fake_x_display": True,
            "os_input": False,
            "gui_capture": False,
            "vizdoom": False,
            "model_calls": 0,
            "docker": False,
        },
        "scope": "one synthetic construction pair through the backend raw-event adapter and InputOwner v12 fake-display harness",
    }
    (OUT / "result.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n",
                                     encoding="utf-8")
    (OUT / "candidate-events.sha256").write_text(sha(raw) + "  candidate-events.jsonl\n",
                                                  encoding="ascii")
    print(json.dumps({"status": result["status"], "run_id": result["run_id"],
                      "events_sha256": result["candidate"]["events_sha256"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
