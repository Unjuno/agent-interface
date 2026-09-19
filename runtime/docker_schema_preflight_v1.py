"""Docker schema preflight over the shared-volume host-model IPC boundary."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runner", type=Path, required=True)
    parser.add_argument("--prompt", type=Path, required=True)
    parser.add_argument("--working", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--instructions", type=Path, required=True)
    parser.add_argument("--schema", type=Path, required=True)
    parser.add_argument("--ipc", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    runner_output = args.output / "runner"
    env = dict(os.environ)
    env["HOST_MODEL_IPC_DIR"] = str(args.ipc.resolve())
    started = time.time_ns()
    command = [
        sys.executable, str(args.runner), "/usr/bin/node", "/usr/bin/true",
        str(args.prompt), str(args.working), str(runner_output), "handle", "-",
        str(args.instructions), str(args.schema),
    ]
    completed = subprocess.run(command, env=env, capture_output=True, text=True)
    report = {
        "schema": "docker_schema_preflight_receipt_v1",
        "status": "PASS" if completed.returncode == 0 else "STOP_RUNNER",
        "returncode": completed.returncode, "authority_granted": False,
        "boundary": "container-to-host-model-ipc", "started_ns": started,
        "stdout": completed.stdout[-2000:], "stderr": completed.stderr[-2000:],
    }
    process_path = runner_output / "process.json"
    events_path = runner_output / "events.jsonl"
    if completed.returncode == 0 and process_path.exists() and events_path.exists():
        events = [json.loads(line) for line in events_path.read_text(encoding="utf-8").splitlines() if line]
        turns = [event for event in events if event.get("type") == "turn.completed"]
        messages = [event for event in events if event.get("type") == "item.completed"]
        report["turns"] = len(turns); report["messages"] = len(messages)
        report["usage"] = turns[0].get("usage") if len(turns) == 1 else None
        if len(turns) != 1 or len(messages) != 1:
            report["status"] = "STOP_MALFORMED_MODEL_RESPONSE"
    elif completed.returncode == 0:
        report["status"] = "STOP_MISSING_RUNNER_RECEIPT"
    (args.output / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
