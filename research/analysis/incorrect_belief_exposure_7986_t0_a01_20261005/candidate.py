"""Candidate-side observation/freshness extractor; deliberately has no truth input."""

import json
import sys
from pathlib import Path


def extract_observations(rows):
    raw = {}
    for row in rows:
        if row["case_id"] in raw:
            raise ValueError("duplicate case_id")
        capture = row["capture_tick"]
        end = row["end_tick"]
        raw[row["case_id"]] = {
            "observation_age_ticks": end - capture,
            "effect_ages_ticks": [event["tick"] - capture for event in row["effects"]],
            "effects": [{"tick": event["tick"], "action": event["action"]} for event in row["effects"]],
        }
    return raw


def main():
    source = json.loads(Path(sys.argv[1]).read_text())
    result = extract_observations(source["candidate_view"])
    Path(sys.argv[2]).write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")


if __name__ == "__main__":
    main()
