from __future__ import annotations

import argparse
import json
import random
from pathlib import Path

ARMS = ("MINIMAL", "SCREENSHOT", "SHAM")
SCHEDULES = {"SENSITIVE": (100, 90), "STABLE": (500, 90)}


def make_trials(seed: int = 652604, blocks: int = 30) -> list[dict]:
    rng = random.Random(seed)
    trials = []
    for block in range(1, blocks+1):
        rows = []
        for schedule, (deadline_ms, action_delay_ms) in SCHEDULES.items():
            for arm in ARMS:
                trial_id = f"b{block:02d}-{schedule.lower()}-{arm.lower()}"
                rows.append({"trial_id": trial_id, "block": block, "schedule": schedule,
                             "arm": arm, "deadline_ms": deadline_ms,
                             "action_delay_ms": action_delay_ms,
                             "action_mode": "save", "expected_value": "committed:"+trial_id})
        rng.shuffle(rows)
        trials.extend(rows)
    return trials


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    parser.add_argument("--seed", type=int, default=652604)
    parser.add_argument("--blocks", type=int, default=30)
    args = parser.parse_args()
    args.output.write_text(json.dumps(make_trials(args.seed, args.blocks), sort_keys=True, indent=2)+"\n")
