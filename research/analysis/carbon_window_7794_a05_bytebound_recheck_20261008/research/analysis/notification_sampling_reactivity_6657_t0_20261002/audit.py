"""Independent interval-based raw auditor for Issue #6657 T0."""
from __future__ import annotations

import copy
import json
import math
import random
import sys
from pathlib import Path


def expected_no_progress(fixture: dict) -> tuple[list[int], list[bool], list[dict]]:
    horizon = fixture["horizon_ticks"]
    progress = fixture["useful_progress_ticks"]
    stale = fixture["stale_after_ticks"]
    ages = [None] * horizon
    # Reconstruct positive-progress ages from each half-open interval, without
    # consulting the candidate's tickwise state loop.
    for left, right in zip(progress, progress[1:]):
        for tick in range(left, min(right, horizon)):
            ages[tick] = tick - left
    for tick in range(progress[-1], horizon):
        ages[tick] = tick - progress[-1]
    if any(age is None for age in ages):
        raise ValueError("fixture leaves an unaccounted clock tick")
    flags = [age > stale for age in ages]
    gaps = [
        {"start_tick": a, "end_tick": b, "duration_ticks": b - a}
        for a, b in zip(progress, progress[1:])
    ]
    return [int(age) for age in ages], flags, gaps


def reconstruct(fixture: dict) -> dict:
    horizon = fixture["horizon_ticks"]
    ages, flags, gaps = expected_no_progress(fixture)
    rng = random.Random(fixture["random_epoch_seed"])
    draws = [rng.randrange(horizon) for _ in range(fixture["random_epoch_draw_count"])]
    arms = {}
    for arm in fixture["notification_arms"]:
        causal_ticks: dict[int, set[str]] = {}
        for tick in fixture["base_check_ticks"]:
            causal_ticks.setdefault(tick, set()).add("base_check")
        if arm["react_to_notifications"] is True:
            latency = fixture["reaction_latency_ticks"]
            for event_tick in arm["notification_ticks"]:
                observed_at = event_tick + latency
                if observed_at in range(horizon):
                    causal_ticks.setdefault(observed_at, set()).add("notification_reaction")
        rows = [
            {"tick": t, "causes": sorted(kinds), "no_progress": flags[t]}
            for t, kinds in sorted(causal_ticks.items())
        ]
        count = sum(bool(row["no_progress"]) for row in rows)
        arms[arm["id"]] = {
            "notification_ticks": arm["notification_ticks"],
            "react_to_notifications": arm["react_to_notifications"],
            "check_ins": rows,
            "checkin_no_progress_count": count,
            "checkin_count": len(rows),
            "checkin_conditioned_no_progress_fraction": count / len(rows) if rows else None,
            "inspection_schedule_informed_by_random_epochs": False,
        }
    sampled = sum(flags[t] for t in draws)
    truth = sum(flags)
    return {
        "schema": "notification-sampling-reactivity-6657-raw-v1",
        "allocation": fixture["allocation"],
        "horizon_ticks": horizon,
        "useful_progress_ticks": fixture["useful_progress_ticks"],
        "age_by_tick": ages,
        "no_progress_by_tick": flags,
        "progress_gaps": gaps,
        "clock_time": {"no_progress_ticks": truth, "denominator_ticks": horizon, "no_progress_fraction": truth / horizon},
        "exogenous_random_epochs": {
            "seed": fixture["random_epoch_seed"],
            "draw_count": len(draws),
            "draw_ticks": draws,
            "sample_no_progress_count": sampled,
            "sample_no_progress_fraction": sampled / len(draws),
            "exact_uniform_epoch_no_progress_fraction": truth / horizon,
            "schedule_visible_to_notification_policy": False,
        },
        "arms": arms,
        "scope": "scripted finite method fixture; not human behavior, a notification effect, or a GUI result",
    }


def same(a, b) -> bool:
    if isinstance(a, bool) or isinstance(b, bool):
        return a is b
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return math.isclose(a, b, rel_tol=0, abs_tol=1e-12)
    if type(a) is not type(b):
        return False
    if isinstance(a, dict):
        return a.keys() == b.keys() and all(same(a[k], b[k]) for k in a)
    if isinstance(a, list):
        return len(a) == len(b) and all(same(x, y) for x, y in zip(a, b))
    return a == b


def validate(fixture: dict, raw: dict) -> bool:
    try:
        return same(reconstruct(fixture), raw)
    except (KeyError, TypeError, ValueError, ZeroDivisionError):
        return False


def audit(fixture: dict, raw: dict) -> dict:
    expected = reconstruct(fixture)
    matched = validate(fixture, raw)
    leaked = copy.deepcopy(raw)
    leaked["arms"]["silent"]["inspection_schedule_informed_by_random_epochs"] = True
    dropped_gap = copy.deepcopy(raw)
    longest = max(dropped_gap["progress_gaps"], key=lambda row: row["duration_ticks"])
    dropped_gap["progress_gaps"].remove(longest)
    controls = {
        "epoch_schedule_leak_rejected": not validate(fixture, leaked),
        "longest_gap_omission_rejected": not validate(fixture, dropped_gap),
    }
    arm_rows = expected["arms"]
    silent = arm_rows["silent"]["check_ins"]
    nonreactive = arm_rows["milestone_visible_nonreactive_control"]["check_ins"]
    reactive_differs = (
        arm_rows["milestone_reactive"]["check_ins"] != silent
        and arm_rows["noisy_status_reactive"]["check_ins"] != silent
    )
    no_reactivity_equal = silent == nonreactive
    clock_equals_exact_random = (
        expected["clock_time"]["no_progress_fraction"]
        == expected["exogenous_random_epochs"]["exact_uniform_epoch_no_progress_fraction"]
    )
    separated_from_at_least_one = any(
        arm_rows[name]["checkin_conditioned_no_progress_fraction"]
        != expected["clock_time"]["no_progress_fraction"]
        for name in ("milestone_reactive", "noisy_status_reactive")
    )
    gates = {
        "raw_reconstruction_exact": matched,
        "all_clock_ticks_counted": len(expected["no_progress_by_tick"]) == fixture["horizon_ticks"],
        "gap_rows_complete": expected["progress_gaps"] == raw.get("progress_gaps"),
        "exact_random_epoch_expectation_matches_truth": clock_equals_exact_random,
        "notification_reactive_schedules_differ": reactive_differs,
        "nonreactive_control_matches_silence": no_reactivity_equal,
        "checkin_and_clock_frames_can_differ": separated_from_at_least_one,
        "mutation_controls_rejected": all(controls.values()),
    }
    return {
        "status": "PASS_METHOD_SCOPED" if all(gates.values()) else "FAIL_METHOD",
        "gates": gates,
        "mutation_controls": controls,
        "clock_time_no_progress_fraction": expected["clock_time"]["no_progress_fraction"],
        "checkin_conditioned_fractions": {
            name: row["checkin_conditioned_no_progress_fraction"] for name, row in arm_rows.items()
        },
        "scope": "finite scripted estimator-separation method only; no human or notification-causality inference",
    }


def main() -> None:
    if len(sys.argv) != 4:
        raise SystemExit("usage: audit.py FIXTURE.json RAW.json AUDIT.json")
    fixture_path, raw_path, output_path = map(Path, sys.argv[1:])
    if output_path.exists():
        raise SystemExit("refusing to overwrite audit output")
    fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
    raw = json.loads(raw_path.read_text(encoding="utf-8"))
    result = audit(fixture, raw)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    raise SystemExit(0 if result["status"] == "PASS_METHOD_SCOPED" else 1)


if __name__ == "__main__":
    main()
