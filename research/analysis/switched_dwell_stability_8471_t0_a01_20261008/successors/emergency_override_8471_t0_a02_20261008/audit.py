"""Independent exhaustive check for the emergency override truth table."""
import copy
import json


def audit(data):
    assert data["schema"] == "8471-a02-emergency-v1"
    assert data["dwell_ticks"] == 10
    expected = []
    for current in ("A", "B"):
        requested = {"A": "B", "B": "A"}[current]
        for elapsed in range(10):
            regular = requested if elapsed >= 10 else current
            selected = requested  # emergency path takes priority on the same tick
            expected.append({"current": current, "requested": requested,
                "elapsed_dwell_ticks": elapsed, "normal_guard_selection": regular,
                "emergency_selection": selected, "delay_ticks": 0,
                "normal_guard_bypassed": selected != regular})
    assert data["rows"] == expected
    assert len(expected) == 20
    return True


def mutations(data):
    changes = {
      "regular_guard_suppresses": lambda row: row.__setitem__("emergency_selection", row["normal_guard_selection"]),
      "hold_current_mode": lambda row: row.__setitem__("emergency_selection", row["current"]),
      "one_tick_delay": lambda row: row.__setitem__("delay_ticks", 1),
    }
    caught = []
    for name, change in changes.items():
        bad = copy.deepcopy(data)
        change(bad["rows"][0])
        try:
            audit(bad)
        except AssertionError:
            caught.append(name)
    assert len(caught) == 3
    return caught


if __name__ == "__main__":
    with open("candidate.json", encoding="utf-8") as f:
        data = json.load(f)
    audit(data)
    print(json.dumps({"audit": "PASS", "rows": 20, "mutations_rejected": mutations(data)}))
