from __future__ import annotations

import json
import random
import threading

SEED = 40120260916
ARMS = ("generic_stable", "generic_switch", "coop_switch", "coop_stable")
N_PER_ARM = 5


def schedule():
    rows = [arm for arm in ARMS for _ in range(N_PER_ARM)]
    random.Random(SEED).shuffle(rows)
    return rows


def run_case(arm: str) -> dict:
    state = {"selection": "A", "A": 0, "B": 0}
    observed_target = state["selection"]

    if arm in {"generic_switch", "coop_switch"}:
        state["selection"] = "B"

    if arm.startswith("generic"):
        state[state["selection"]] += 2
        accepted = True
    else:
        # Mechanism under test: expected-target validation and mutation occur
        # inside one serialized semantic critical section.
        lock = threading.Lock()
        with lock:
            if state["selection"] != observed_target:
                accepted = False
            else:
                state[state["selection"]] += 2
                accepted = True

    return {
        "arm": arm,
        "observed_target": observed_target,
        "selection_at_commit": state["selection"],
        "accepted": accepted,
        "A_delta": state["A"],
        "B_delta": state["B"],
    }


def main():
    results = [run_case(arm) for arm in schedule()]
    print(json.dumps({"seed": SEED, "results": results}, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
