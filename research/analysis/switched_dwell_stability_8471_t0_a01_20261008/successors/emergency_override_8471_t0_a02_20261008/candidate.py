"""A02 finite truth table for emergency bypass of a ten-tick dwell guard."""
import json
from pathlib import Path


def normal_guard(current, requested, elapsed, dwell=10):
    return requested if requested != current and elapsed >= dwell else current


def emergency_select(current, requested):
    """Emergency semantics are an unconditional same-tick selection."""
    return requested


def main():
    rows = []
    for current in ("A", "B"):
        requested = "B" if current == "A" else "A"
        for elapsed in range(10):
            regular = normal_guard(current, requested, elapsed)
            selected = emergency_select(current, requested)
            rows.append({"current": current, "requested": requested,
                "elapsed_dwell_ticks": elapsed, "normal_guard_selection": regular,
                "emergency_selection": selected,
                "delay_ticks": 0 if selected == requested else None,
                "normal_guard_bypassed": selected != regular})
    Path("candidate.json").write_text(json.dumps({"schema": "8471-a02-emergency-v1",
        "dwell_ticks": 10, "rows": rows}, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
