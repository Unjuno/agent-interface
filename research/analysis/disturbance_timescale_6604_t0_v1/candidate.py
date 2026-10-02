"""Deterministic no-model candidate for Issue #6604 T0."""

from __future__ import annotations

import json
import sys
from pathlib import Path


HORIZON = 12
ACTION_LIMIT = 2
POSITION_LIMITS = (-24, 24)


def clamp(value: int, low: int, high: int) -> int:
    return max(low, min(high, value))


def rollout(case: dict, route: str) -> dict:
    targets = case["targets"]
    if len(targets) != HORIZON:
        raise ValueError("target schedule has wrong horizon")
    position = 0
    delayed_command = 0
    rows = []
    for tick, numeric_target in enumerate(targets):
        if route == "direct":
            sample_tick = (tick // 3) * 3
            observed_target = targets[sample_tick]
            command = clamp(observed_target - position, -ACTION_LIMIT, ACTION_LIMIT)
            applied = command
            observation_age = tick - sample_tick
        elif route == "local_periodic":
            observed_target = numeric_target
            command = clamp(observed_target - position, -ACTION_LIMIT, ACTION_LIMIT)
            applied = delayed_command
            delayed_command = command
            observation_age = 0
        else:
            raise ValueError(f"unknown route {route}")
        before = position
        position = clamp(position + applied, *POSITION_LIMITS)
        rows.append(
            {
                "tick": tick,
                "observation_age": observation_age,
                "observed_target": observed_target,
                "position_before": before,
                "command": command,
                "applied": applied,
                "position_after": position,
                "tracking_error": abs(numeric_target - position),
            }
        )
    release_lag = 0 if route == "direct" else 1
    release_applied = 0 if route == "direct" else delayed_command
    release_position = clamp(position + release_applied, *POSITION_LIMITS)
    release_error = abs(targets[-1] - release_position)
    return {
        "case_id": case["id"],
        "route": route,
        "rows": rows,
        "tracking_error_sum": sum(row["tracking_error"] for row in rows) + release_error,
        "action_count": len(rows),
        "release_lag_ticks": release_lag,
        "release": {
            "requested_at_tick": HORIZON,
            "neutral_at_tick": HORIZON + release_lag,
            "residual_command_applied": release_applied,
            "position_after_release": release_position,
            "terminal_neutral": True,
        },
        "terminal_neutral": True,
    }


def run(cases: dict) -> dict:
    records = [rollout(case, route) for case in cases["cases"] for route in ("direct", "local_periodic")]
    return {"schema": "issue6604-t0-candidate-v1", "records": records}


def main() -> int:
    cases_path, output_path = map(Path, sys.argv[1:3])
    result = run(json.loads(cases_path.read_text()))
    output_path.write_text(json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n")
    print(f"rows={len(result['records'])} status=COMPLETE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
