"""Bound owner-commanded key hold intervals from retained event logs.

This analyzer is intentionally narrow. It is valid for the retained session lineage
where a `hold` step:

1. acknowledges each key-down through InputOwner,
2. performs synchronous observations while the keys remain owned,
3. releases keys in the hold's `finally` block, and
4. takes one final observation after release before `step_completed`.

For an ordinary completed hold, the last in-hold observation's
`artifact_ready_ns` is therefore a lower bound on when the owner can issue the
key-up, while the final post-release observation's `capture_ns` is an upper
bound on completion of the owner's key-up + X11 sync call.

These are owner-commanded OS-input bounds, not proof of continuous physical
key-map occupancy. An external actor could theoretically inject a key-up between
samples, and the retained v39 trace does not poll query_keymap continuously.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from statistics import median


SCHEMA = "held-input-telemetry-bound-v1"


def load_events(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def command_steps(events: list[dict]) -> dict[tuple[str, int], dict]:
    out: dict[tuple[str, int], dict] = {}
    for row in events:
        if row.get("event") != "command":
            continue
        cmd = row.get("command", {})
        if cmd.get("op") != "submit":
            continue
        for index, step in enumerate(cmd.get("steps", [])):
            out[(cmd["id"], index)] = step
    return out


def analyze(events: list[dict]) -> dict:
    steps = command_steps(events)
    active: dict | None = None
    completed: list[dict] = []
    interrupted: list[dict] = []

    for row in events:
        event = row.get("event")

        if event == "step_started" and row.get("operation") == "hold":
            key = (row["id"], row["step"])
            step = steps.get(key)
            if not isinstance(step, dict) or step.get("op") != "hold":
                raise AssertionError(f"missing hold command for {key}")
            if active is not None:
                raise AssertionError("overlapping hold steps are outside this analyzer")
            active = {
                "id": row["id"],
                "step": row["step"],
                "requested_ms": step["duration_ms"],
                "keys": list(step["keys"]),
                "down_acks": [],
                "observations": [],
                "keys_held_marker_ns": None,
            }
            continue

        if active is None:
            continue

        if event == "input_admission":
            # Retained owner-v10 keyboard admission rows do not carry id/step;
            # executor serialization means they belong to the one active hold.
            active["down_acks"].append(row["input_ack_ns"])
            continue

        if event == "keys_held":
            if row.get("id") == active["id"] and row.get("step") == active["step"]:
                active["keys_held_marker_ns"] = row["input_ack_ns"]
            continue

        if event == "observation":
            if row.get("id") == active["id"] and row.get("step") == active["step"]:
                active["observations"].append(row)
            continue

        if event == "input_released" and row.get("id") == active["id"]:
            owner_release = row.get("owner_release", {})
            if owner_release.get("verified") is True:
                if not active["down_acks"]:
                    raise AssertionError("interrupted hold has no down acknowledgement")
                interrupted.append({
                    "id": active["id"],
                    "step": active["step"],
                    "requested_ms": active["requested_ms"],
                    "keys": active["keys"],
                    "full_keyset_ack_ns": max(active["down_acks"]),
                    "empty_verified_ns": owner_release["verified_ns"],
                    "ack_to_empty_verified_ms": (
                        owner_release["verified_ns"] - max(active["down_acks"])
                    ) / 1e6,
                    "classification": "interrupted_empty_verified",
                })
            continue

        if event == "step_completed" and row.get("id") == active["id"] and row.get("step") == active["step"]:
            if len(active["down_acks"]) != len(active["keys"]):
                raise AssertionError(
                    f"{active['id']}:{active['step']} expected {len(active['keys'])} "
                    f"down acknowledgements, got {len(active['down_acks'])}"
                )
            if len(active["observations"]) < 2:
                raise AssertionError("completed hold needs in-hold and post-release observations")

            # Source-order contract: penultimate observation is the last one
            # completed before ordinary key-up; final observation is captured
            # after key-up + X11 sync and before step_completed.
            before_release = active["observations"][-2]
            after_release = active["observations"][-1]
            release_lower_ns = before_release["artifact_ready_ns"]
            release_upper_ns = after_release["capture_ns"]
            full_ack_ns = max(active["down_acks"])
            if not (full_ack_ns <= release_lower_ns <= release_upper_ns <= row["completed_ns"]):
                raise AssertionError("invalid retained timing order")

            lower_ms = (release_lower_ns - full_ack_ns) / 1e6
            upper_ms = (release_upper_ns - full_ack_ns) / 1e6
            completed.append({
                "id": active["id"],
                "step": active["step"],
                "requested_ms": active["requested_ms"],
                "keys": active["keys"],
                "full_keyset_ack_ns": full_ack_ns,
                "release_issue_lower_ns": release_lower_ns,
                "release_complete_upper_ns": release_upper_ns,
                "owner_commanded_hold_lower_ms": lower_ms,
                "owner_commanded_hold_upper_ms": upper_ms,
                "overshoot_lower_ms": lower_ms - active["requested_ms"],
                "overshoot_upper_ms": upper_ms - active["requested_ms"],
                "bound_width_ms": (release_upper_ns - release_lower_ns) / 1e6,
                "classification": "ordinary_completed_bounded",
            })
            active = None
            continue

        if event == "terminal" and row.get("id") == active["id"]:
            # Interrupted holds never emit step_completed. Their verified-empty
            # evidence was already captured from input_released when available.
            active = None

    requested = sum(row["requested_ms"] for row in completed)
    lower = sum(row["owner_commanded_hold_lower_ms"] for row in completed)
    upper = sum(row["owner_commanded_hold_upper_ms"] for row in completed)
    result = {
        "schema": SCHEMA,
        "completed_holds": completed,
        "interrupted_holds": interrupted,
        "summary": {
            "completed_hold_count": len(completed),
            "interrupted_verified_count": len(interrupted),
            "requested_total_ms": requested,
            "owner_commanded_hold_total_lower_ms": lower,
            "owner_commanded_hold_total_upper_ms": upper,
            "overshoot_total_lower_ms": lower - requested,
            "overshoot_total_upper_ms": upper - requested,
            "overshoot_fraction_lower": ((lower - requested) / requested) if requested else None,
            "overshoot_fraction_upper": ((upper - requested) / requested) if requested else None,
            "median_overshoot_lower_ms": median(
                row["overshoot_lower_ms"] for row in completed
            ) if completed else None,
            "median_overshoot_upper_ms": median(
                row["overshoot_upper_ms"] for row in completed
            ) if completed else None,
        },
        "limitations": [
            "bounds owner-commanded X11 input, not continuous query_keymap occupancy",
            "requires the retained session-v4/session-v5 hold source ordering",
            "does not identify task-useful effect",
            "does not turn v38/v39 into a causal comparison",
        ],
    }
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("events", type=Path)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    result = analyze(load_events(args.events))
    encoded = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.write_text(encoded, encoding="utf-8")
    else:
        print(encoded, end="")


if __name__ == "__main__":
    main()
