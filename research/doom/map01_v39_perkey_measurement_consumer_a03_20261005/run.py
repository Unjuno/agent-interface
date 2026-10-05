"""One-shot replay using only machine-generated freeze identities."""
from __future__ import annotations
import hashlib
import json
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from candidate import load_events, reconstruct

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
OUT = HERE / "results" / "a03"


def main() -> None:
    freeze_path = HERE / "FREEZE.json"
    freeze_bytes = freeze_path.read_bytes()
    freeze = json.loads(freeze_bytes)
    for relative, expected in freeze["source_sha256"].items():
        observed = hashlib.sha256((HERE / relative).read_bytes()).hexdigest()
        if observed != expected:
            raise RuntimeError("frozen source hash mismatch: " + relative)
    raw, events = load_events(HERE / "INPUT_EVENTS.jsonl", freeze_path)
    source = freeze["source_input"]
    relative = source["path"]
    blob = subprocess.run(
        ["git", "hash-object", relative], cwd=REPO, check=True,
        text=True, capture_output=True
    ).stdout.strip()
    if blob != source["git_blob"]:
        raise RuntimeError("input Git blob does not match generated freeze")
    result = reconstruct(events)
    if OUT.exists():
        raise FileExistsError("one-shot output path already exists")
    started_ns = time.time_ns()
    started = datetime.now(timezone.utc).isoformat()
    OUT.mkdir(parents=True, exist_ok=False)
    payload = {
        "run_id": freeze["run_id"],
        "status": "PASS_MEASUREMENT_CONSUMER_SCOPED",
        "started_utc": started,
        "finished_utc": datetime.now(timezone.utc).isoformat(),
        "started_unix_ns": started_ns,
        "finished_unix_ns": time.time_ns(),
        "input_sha256": hashlib.sha256(raw).hexdigest(),
        "freeze_sha256": hashlib.sha256(freeze_bytes).hexdigest(),
        "input_event_count": len(events),
        "candidate": result,
        "environment": {
            "host": "offline retained-data replay",
            "new_os_input": False,
            "new_gui_or_game": False,
            "new_model_call": False,
            "container": False
        }
    }
    (OUT / "RESULT.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps(payload, sort_keys=True))


if __name__ == "__main__":
    main()
