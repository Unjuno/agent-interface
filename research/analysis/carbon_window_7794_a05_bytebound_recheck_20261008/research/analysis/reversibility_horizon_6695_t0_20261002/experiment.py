"""Frozen deterministic candidate for Issue #6695 T0."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

POLICIES = ("IMMEDIATE", "STAGE_1", "STAGE_2")
STRATA = {
    "informative_signal_1": {"truth": "B", "proposal": "A", "s1": "B", "s2": "B", "route": True, "deadline": 3},
    "uninformative": {"truth": "B", "proposal": "A", "s1": "UNKNOWN", "s2": "UNKNOWN", "route": True, "deadline": 3},
    "informative_signal_2": {"truth": "B", "proposal": "A", "s1": "UNKNOWN", "s2": "B", "route": True, "deadline": 3},
    "no_correction_route": {"truth": "B", "proposal": "A", "s1": "B", "s2": "B", "route": False, "deadline": 3},
}


def run_one(stratum: str, repetition: int, policy: str) -> dict:
    spec = STRATA[stratum]
    events = []
    target = spec["proposal"]
    if policy == "IMMEDIATE":
        events.append({"t": 0, "op": "commit", "target": target})
    else:
        events.append({"t": 0, "op": "prepare", "target": target, "reversible": True})
        observed = [spec["s1"]]
        events.append({"t": 1, "op": "observe", "signal": spec["s1"]})
        if policy == "STAGE_2":
            observed.append(spec["s2"])
            events.append({"t": 2, "op": "observe", "signal": spec["s2"]})
        latest = next((s for s in reversed(observed) if s != "UNKNOWN"), target)
        if spec["route"]:
            target = latest
        commit_t = 1 if policy == "STAGE_1" else 2
        events.append({"t": commit_t, "op": "commit", "target": target})
    commit = next(e for e in events if e["op"] == "commit")
    return {
        "case_id": f"rh6695-{stratum}-{repetition:03d}-{policy.lower()}",
        "stratum": stratum,
        "repetition": repetition,
        "policy": policy,
        "truth": spec["truth"],
        "proposal": spec["proposal"],
        "signals": [spec["s1"], spec["s2"]],
        "correction_route": spec["route"],
        "deadline": spec["deadline"],
        "events": events,
        "committed_target": commit["target"],
        "wrong_irreversible": commit["target"] != spec["truth"],
        "deadline_miss": commit["t"] > spec["deadline"],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    path = Path(args.out)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        for stratum in STRATA:
            for repetition in range(1):
                for policy in POLICIES:
                    stream.write(json.dumps(run_one(stratum, repetition, policy), sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
