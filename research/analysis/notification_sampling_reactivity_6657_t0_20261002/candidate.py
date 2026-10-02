"""Finite notification-conditioned inspection-sampling candidate for #6657."""
from __future__ import annotations

import json
import random
import sys
from pathlib import Path


def build_raw(fixture: dict) -> dict:
    horizon = fixture["horizon_ticks"]
    progress = fixture["useful_progress_ticks"]
    stale_after = fixture["stale_after_ticks"]
    no_progress = []
    age_by_tick = []
    latest = progress[0]
    cursor = 0
    for tick in range(horizon):
        while cursor + 1 < len(progress) and progress[cursor + 1] <= tick:
            cursor += 1
            latest = progress[cursor]
        age = tick - latest
        age_by_tick.append(age)
        no_progress.append(age > stale_after)

    rng = random.Random(fixture["random_epoch_seed"])
    draws = [rng.randrange(horizon) for _ in range(fixture["random_epoch_draw_count"])]
    arms = {}
    for arm in fixture["notification_arms"]:
        causes: dict[int, list[str]] = {}
        for tick in fixture["base_check_ticks"]:
            causes.setdefault(tick, []).append("base_check")
        if arm["react_to_notifications"]:
            for tick in arm["notification_ticks"]:
                check_tick = tick + fixture["reaction_latency_ticks"]
                if 0 <= check_tick < horizon:
                    causes.setdefault(check_tick, []).append("notification_reaction")
        checks = [
            {"tick": tick, "causes": sorted(check_causes), "no_progress": no_progress[tick]}
            for tick, check_causes in sorted(causes.items())
        ]
        arms[arm["id"]] = {
            "notification_ticks": arm["notification_ticks"],
            "react_to_notifications": arm["react_to_notifications"],
            "check_ins": checks,
            "checkin_no_progress_count": sum(row["no_progress"] for row in checks),
            "checkin_count": len(checks),
            "checkin_conditioned_no_progress_fraction": (
                sum(row["no_progress"] for row in checks) / len(checks) if checks else None
            ),
            "inspection_schedule_informed_by_random_epochs": False,
        }

    gaps = []
    for left, right in zip(progress, progress[1:]):
        gaps.append({"start_tick": left, "end_tick": right, "duration_ticks": right - left})
    random_sample_count = sum(no_progress[tick] for tick in draws)
    clock_count = sum(no_progress)
    return {
        "schema": "notification-sampling-reactivity-6657-raw-v1",
        "allocation": fixture["allocation"],
        "horizon_ticks": horizon,
        "useful_progress_ticks": progress,
        "age_by_tick": age_by_tick,
        "no_progress_by_tick": no_progress,
        "progress_gaps": gaps,
        "clock_time": {
            "no_progress_ticks": clock_count,
            "denominator_ticks": horizon,
            "no_progress_fraction": clock_count / horizon,
        },
        "exogenous_random_epochs": {
            "seed": fixture["random_epoch_seed"],
            "draw_count": len(draws),
            "draw_ticks": draws,
            "sample_no_progress_count": random_sample_count,
            "sample_no_progress_fraction": random_sample_count / len(draws),
            "exact_uniform_epoch_no_progress_fraction": clock_count / horizon,
            "schedule_visible_to_notification_policy": False,
        },
        "arms": arms,
        "scope": "scripted finite method fixture; not human behavior, a notification effect, or a GUI result",
    }


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("usage: candidate.py FIXTURE.json RAW.json")
    fixture_path, output_path = map(Path, sys.argv[1:])
    if output_path.exists():
        raise SystemExit("refusing to overwrite candidate raw")
    raw = build_raw(json.loads(fixture_path.read_text(encoding="utf-8")))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(raw, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    print(json.dumps({"allocation": raw["allocation"], "arms": len(raw["arms"]), "ticks": raw["horizon_ticks"]}))


if __name__ == "__main__":
    main()
