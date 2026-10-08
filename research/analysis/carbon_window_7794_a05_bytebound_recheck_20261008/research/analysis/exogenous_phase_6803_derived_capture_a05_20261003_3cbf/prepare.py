"""Prepare source-only authored cells before the source freeze (no outcomes)."""
import argparse
import json
from pathlib import Path


def fixture():
    def make(identity, onset=9, expiry=20, **changes):
        item = {"case_id": identity, "opportunity": {"onset_ms": onset, "expiry_ms": expiry},
                "capture_schedule_ms": [10, 50], "observation_horizon_ms": 60,
                "clock_synchronized": True, "delivery_latency_ms": 1,
                "decision_latency_ms": 1, "effect_latency_ms": 0,
                "effect_enabled": True, "safe_stop": False}
        item.update(changes)
        return item
    cells = [make(f"grid-e{expiry}-o{onset:02}", onset, expiry)
             for expiry in (20, 51, 60) for onset in range(expiry + 1)]
    cells += [make("control-no-cue", opportunity=None),
              make("control-unsynced", clock_synchronized=False),
              make("control-late-delivery", delivery_latency_ms=11),
              make("control-late-decision", decision_latency_ms=10),
              make("control-no-effect", effect_enabled=False),
              make("control-safe-stop", safe_stop=True),
              make("control-right-censor", observation_horizon_ms=15, effect_latency_ms=10),
              make("control-late-effect", effect_latency_ms=10),
              make("control-before-capture", observation_horizon_ms=9),
              make("control-expiry-equality", expiry=10),
              make("control-zero-latency", onset=10, expiry=10,
                   delivery_latency_ms=0, decision_latency_ms=0),
              make("duration-hit", onset=9, expiry=11, delivery_latency_ms=0, decision_latency_ms=0),
              make("duration-miss", onset=11, expiry=13, delivery_latency_ms=0, decision_latency_ms=0)]
    return {"schema": "derived-capture-input-v1", "fixture_id": "FIXTURE-6969-A05-3CBF", "cases": cells}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    with Path(args.out).open("x") as target:
        json.dump(fixture(), target, sort_keys=True, indent=2)
        target.write("\n")
    print("PREPARED rows=147; no capture membership or verdict labels")
