import json
import time
from pathlib import Path

from ledger import summarize


HERE = Path(__file__).resolve().parent
OUT = HERE / "results" / "t0-01" / "raw.json"
ALLOCATION = "MAP01-PER-KEY-OCCUPANCY-LEDGER-59-T0-20261001-01"
MAIN = "6cd70ad4bfad74e11658057bf024918bffb24add"


def frozen_rows():
    return [
        {
            "kind": "key_interval", "action_id": "act-1", "epoch": 7,
            "key": "W", "press_request_ns": 100, "press_sync_ns": 110,
            "down_sample_ns": 111, "release_request_ns": 180,
            "release_sync_ns": 190, "up_sample_ns": 191,
            "source": "input-owner-v11",
        },
        {
            "kind": "key_interval", "action_id": "act-1", "epoch": 7,
            "key": "SPACE", "press_request_ns": 120, "press_sync_ns": 128,
            "down_sample_ns": 129, "release_request_ns": 160,
            "release_sync_ns": 170, "up_sample_ns": 171,
            "source": "input-owner-v11",
        },
        {
            "kind": "verified_empty", "action_id": "act-1", "epoch": 7,
            "timestamp_ns": 200, "keys_down": [], "source": "xquerykeymap",
        },
    ]


def main():
    started = time.monotonic_ns()
    events = frozen_rows()
    result = summarize(events)
    finished = time.monotonic_ns()
    output = {
        "schema": "map01-per-key-occupancy-ledger-t0-v1",
        "allocation_id": ALLOCATION,
        "main_sha": MAIN,
        "events": events,
        "candidate_result": result,
        "candidate_invocations": 1,
        "started_monotonic_ns": started,
        "finished_monotonic_ns": finished,
    }
    OUT.parent.mkdir(parents=True, exist_ok=False)
    OUT.write_text(json.dumps(output, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"raw_path": str(OUT), "status": result["status"],
                      "intervals": result["intervals"]}, sort_keys=True))


if __name__ == "__main__":
    main()
