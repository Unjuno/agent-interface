"""One-shot replay of the frozen per-key measurement consumer."""
from __future__ import annotations
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from candidate import load_events, reconstruct

HERE = Path(__file__).resolve().parent
OUT = HERE / "results" / "a02"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=False)
    started_ns = time.time_ns()
    started = datetime.now(timezone.utc).isoformat()
    raw, events = load_events(HERE / "INPUT_EVENTS.jsonl")
    result = reconstruct(events)
    finished_ns = time.time_ns()
    payload = {
        "run_id": "MAP01-V39-PERKEY-MEASUREMENT-CONSUMER-A02-20261005",
        "status": "PASS_MEASUREMENT_CONSUMER_SCOPED",
        "started_utc": started,
        "finished_utc": datetime.now(timezone.utc).isoformat(),
        "started_unix_ns": started_ns,
        "finished_unix_ns": finished_ns,
        "input_sha256": __import__("hashlib").sha256(raw).hexdigest(),
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
