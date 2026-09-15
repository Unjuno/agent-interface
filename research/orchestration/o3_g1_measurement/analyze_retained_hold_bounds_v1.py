"""Reconstruct delivered all-key hold occupancy bounds from retained MAP01 traces.

This intentionally does not promote program lifetime to physical input lifetime.
For normally completed hold steps on the frozen session_v4 execution path:
- `keys_held.input_ack_ns` is the X11-sync acknowledgement after all requested
  keys have been pressed.
- the hold deadline is created only after the `keys_held` event callback returns,
  so `keys_held.emit_ns + duration_ms` is a conservative lower bound on release.
- the backend releases keys in `finally` before taking one final per-step snapshot,
  so the last observation capture before `step_completed` is an upper bound on
  ordinary key release.

Cancellation/expiry paths do not preserve the requested-duration lower bound.
For those, the analyzer reports only an empty-state verification upper bound.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Iterable

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
DOOM_RESULTS = REPO / "research" / "doom" / "results"
DEFAULT_RUNS = (
    "map01-v38-integrated-threat-live-01",
    "map01-v39-coast-liveness-live-01",
)


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def overlap_ns(a0: int, a1: int, b0: int, b1: int) -> int:
    if a1 < a0 or b1 < b0:
        raise ValueError("invalid interval")
    return max(0, min(a1, b1) - max(a0, b0))


def ms(ns: int) -> float:
    return round(ns / 1_000_000, 3)


def command_map(events: Iterable[dict]) -> dict[str, dict]:
    result = {}
    for row in events:
        if row.get("event") != "command":
            continue
        command = row.get("command")
        if isinstance(command, dict) and command.get("op") == "submit":
            identifier = command.get("id")
            if not isinstance(identifier, str) or not identifier:
                raise ValueError("submit command missing id")
            if identifier in result:
                raise ValueError(f"duplicate submit id: {identifier}")
            result[identifier] = command
    return result


def event_index(events: Iterable[dict], event_name: str) -> dict[tuple[str, int], list[dict]]:
    result: dict[tuple[str, int], list[dict]] = {}
    for row in events:
        if row.get("event") != event_name:
            continue
        identifier, step = row.get("id"), row.get("step")
        if not isinstance(identifier, str) or type(step) is not int:
            continue
        result.setdefault((identifier, step), []).append(row)
    return result


def terminal_empty_upper(events: Iterable[dict], identifier: str) -> tuple[int | None, str | None]:
    """Return earliest retained empty-state verification for an interrupted program."""
    candidates: list[tuple[int, str]] = []
    for row in events:
        if row.get("id") != identifier:
            continue
        if row.get("event") == "input_released":
            release = row.get("owner_release")
            if isinstance(release, dict) and release.get("verified") is True:
                value = release.get("verified_ns")
                if type(value) is int:
                    candidates.append((value, "input_released.owner_release.verified_ns"))
        if row.get("event") == "terminal":
            interruption = row.get("interruption")
            if isinstance(interruption, dict):
                record = interruption.get("record")
                if isinstance(record, dict) and record.get("verified") is True:
                    value = record.get("verified_ns")
                    if type(value) is int:
                        candidates.append((value, "terminal.interruption.record.verified_ns"))
            release = row.get("release")
            if isinstance(release, dict) and release.get("verified") is True:
                value = release.get("verified_ns")
                if type(value) is int:
                    candidates.append((value, "terminal.release.verified_ns"))
    return min(candidates) if candidates else (None, None)


def analyze_events(report: dict, events: list[dict], run_name: str = "synthetic") -> dict:
    commands = command_map(events)
    held = event_index(events, "keys_held")
    observations = event_index(events, "observation")
    completed = event_index(events, "step_completed")

    decisions = report.get("decisions")
    if not isinstance(decisions, list):
        raise ValueError("report decisions missing")

    waits = []
    for decision in decisions:
        start, end = decision.get("controller_model_started_ns"), decision.get("controller_model_ended_ns")
        if type(start) is not int or type(end) is not int or not start < end:
            raise ValueError("invalid controller model wait")
        waits.append((decision.get("iteration"), start, end))

    hold_rows = []
    for identifier, command in commands.items():
        steps = command.get("steps")
        if not isinstance(steps, list):
            raise ValueError(f"{identifier}: steps missing")
        for step_index, step in enumerate(steps):
            if not isinstance(step, dict) or step.get("op") != "hold":
                continue
            duration_ms = step.get("duration_ms")
            if type(duration_ms) not in (int, float) or not duration_ms > 0:
                raise ValueError(f"{identifier}:{step_index}: invalid duration")
            held_rows = held.get((identifier, step_index), [])
            if len(held_rows) > 1:
                raise ValueError(f"{identifier}:{step_index}: multiple keys_held events")
            if not held_rows:
                hold_rows.append({
                    "id": identifier,
                    "step": step_index,
                    "status": "not_started",
                    "keys": step.get("keys"),
                    "requested_duration_ms": duration_ms,
                })
                continue

            start_row = held_rows[0]
            start_ns = start_row.get("input_ack_ns")
            emit_ns = start_row.get("emit_ns")
            if type(start_ns) is not int or type(emit_ns) is not int or emit_ns < start_ns:
                raise ValueError(f"{identifier}:{step_index}: invalid keys_held clocks")

            done_rows = completed.get((identifier, step_index), [])
            if len(done_rows) > 1:
                raise ValueError(f"{identifier}:{step_index}: multiple step_completed events")

            row = {
                "id": identifier,
                "step": step_index,
                "status": None,
                "keys": start_row.get("keys"),
                "requested_duration_ms": duration_ms,
                "all_keys_down_ack_ns": start_ns,
            }
            if done_rows:
                done_ns = done_rows[0].get("completed_ns")
                if type(done_ns) is not int:
                    raise ValueError(f"{identifier}:{step_index}: invalid step completion")
                obs = [value for value in observations.get((identifier, step_index), [])
                       if type(value.get("capture_ns")) is int and value["capture_ns"] <= done_ns]
                if not obs:
                    raise ValueError(f"{identifier}:{step_index}: completed hold lacks final observation")
                final_capture_ns = max(value["capture_ns"] for value in obs)
                release_lower_ns = emit_ns + int(round(duration_ms * 1_000_000))
                release_upper_ns = final_capture_ns
                if not start_ns <= release_lower_ns <= release_upper_ns <= done_ns:
                    raise ValueError(
                        f"{identifier}:{step_index}: release bound ordering failed "
                        f"{start_ns} <= {release_lower_ns} <= {release_upper_ns} <= {done_ns}")
                row.update({
                    "status": "completed_release_bounded",
                    "release_lower_ns": release_lower_ns,
                    "release_upper_ns": release_upper_ns,
                    "release_bound_width_ms": ms(release_upper_ns - release_lower_ns),
                    "all_keys_down_duration_lower_ms": ms(release_lower_ns - start_ns),
                    "all_keys_down_duration_upper_ms": ms(release_upper_ns - start_ns),
                    "release_upper_evidence": "last_step_observation.capture_ns",
                })
            else:
                upper_ns, evidence = terminal_empty_upper(events, identifier)
                if upper_ns is None or upper_ns < start_ns:
                    row.update({
                        "status": "started_release_unbounded",
                        "release_lower_ns": start_ns,
                        "release_upper_ns": None,
                        "release_bound_width_ms": None,
                        "release_upper_evidence": None,
                    })
                else:
                    # Cancellation can pre-empt requested duration. Only non-negative
                    # occupancy and the verified-empty upper bound are retained.
                    row.update({
                        "status": "interrupted_empty_upper_bounded",
                        "release_lower_ns": start_ns,
                        "release_upper_ns": upper_ns,
                        "release_bound_width_ms": ms(upper_ns - start_ns),
                        "all_keys_down_duration_lower_ms": 0.0,
                        "all_keys_down_duration_upper_ms": ms(upper_ns - start_ns),
                        "release_upper_evidence": evidence,
                    })

            if row["release_upper_ns"] is not None:
                overlaps = []
                for iteration, wait_start, wait_end in waits:
                    lower = overlap_ns(start_ns, row["release_lower_ns"], wait_start, wait_end)
                    upper = overlap_ns(start_ns, row["release_upper_ns"], wait_start, wait_end)
                    if lower or upper:
                        overlaps.append({
                            "iteration": iteration,
                            "model_wait_overlap_lower_ms": ms(lower),
                            "model_wait_overlap_upper_ms": ms(upper),
                        })
                row["model_wait_overlaps"] = overlaps
            hold_rows.append(row)

    completed_bounds = [row for row in hold_rows if row.get("status") == "completed_release_bounded"]
    lower_coverage_ns = upper_coverage_ns = 0
    for row in completed_bounds:
        for value in row.get("model_wait_overlaps", []):
            lower_coverage_ns += int(round(value["model_wait_overlap_lower_ms"] * 1_000_000))
            upper_coverage_ns += int(round(value["model_wait_overlap_upper_ms"] * 1_000_000))

    independent_timed = [
        row for row in events
        if row.get("event") in {
            "independent_useful_effect",
            "independent_progress",
            "independent_semantic_completion",
        } and any(type(row.get(field)) is int for field in ("known_ns", "capture_ns", "emit_ns"))
    ]
    post_scores = [row for row in events if row.get("event") == "post_control_score"]

    widths = [row["release_bound_width_ms"] for row in completed_bounds]
    return {
        "schema": "o3-g1-retained-hold-bounds-v1",
        "run": run_name,
        "hold_steps": hold_rows,
        "summary": {
            "hold_steps_total": len(hold_rows),
            "completed_release_bounded": len(completed_bounds),
            "interrupted_started": sum(row.get("status") == "interrupted_empty_upper_bounded" for row in hold_rows),
            "not_started": sum(row.get("status") == "not_started" for row in hold_rows),
            "release_bound_width_ms_median": (
                round(sorted(widths)[len(widths) // 2], 3) if widths else None
            ),
            "release_bound_width_ms_max": max(widths) if widths else None,
            "model_wait_all_keys_down_coverage_lower_ms": ms(lower_coverage_ns),
            "model_wait_all_keys_down_coverage_upper_ms": ms(upper_coverage_ns),
            "timed_independent_useful_events": len(independent_timed),
            "terminal_independent_score_events": len(post_scores),
            "first_independent_useful_outcome_time": (
                "available" if independent_timed else "unavailable"
            ),
        },
        "limits": [
            "release is interval-bounded, not directly timestamped at ordinary key-up X11 sync",
            "keys_held binds the all-key chord to id/step; individual input_admission rows are not id/step-bound in retained v38/v39",
            "X11 sync/queried empty input is not proof the application consumed a semantic action",
            "post_control_score is terminal and cannot timestamp first independently useful effect",
        ],
    }


def analyze_run(root: Path, run_name: str) -> dict:
    run = root / run_name
    report_path = run / "report.json"
    event_path = run / "runtime" / "events.jsonl"
    result = analyze_events(read_json(report_path), read_jsonl(event_path), run_name)
    result["source_sha256"] = {
        "report.json": sha256(report_path),
        "runtime/events.jsonl": sha256(event_path),
    }
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--results-root", type=Path, default=DOOM_RESULTS)
    parser.add_argument("--run", action="append", dest="runs")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    names = tuple(args.runs) if args.runs else DEFAULT_RUNS
    result = {
        "schema": "o3-g1-retained-hold-bounds-collection-v1",
        "runs": [analyze_run(args.results_root, name) for name in names],
        "scope": "retained offline reconstruction; no model, GUI, OS-input or new live allocation",
    }
    encoded = json.dumps(result, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded, encoding="utf-8", newline="\n")
    else:
        print(encoded, end="")


if __name__ == "__main__":
    main()
