"""Interval-censored physical-key occupancy from retained MAP01 runtime events.

The retained X11 owner logs key-down acknowledgements but normal key-up calls do
not emit a timestamp.  This module therefore never claims an exact hold duration.
For each hold step it derives:

* a certified any-key-down interval: first input acknowledgement -> latest time
  at which the runtime semantics prove at least one requested key was still held;
* a possible occupancy envelope: earliest admission attempt -> a time by which
  release is proven complete.

The physical occupancy lies between those two durations.  Aggregates preserve
that interval rather than substituting the programmed hold duration.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import defaultdict
from pathlib import Path
from typing import Iterable


def ms(ns: int) -> float:
    return round(ns / 1e6, 3)


def overlap_ns(a: int, b: int, c: int, d: int) -> int:
    return max(0, min(b, d) - max(a, c))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def submit_steps(events: Iterable[dict]) -> dict[tuple[str, int], dict]:
    holds: dict[tuple[str, int], dict] = {}
    for row in events:
        command = row.get("command", {})
        if row.get("event") != "command" or command.get("op") != "submit":
            continue
        identifier = command["id"]
        for index, step in enumerate(command["steps"]):
            if step.get("op") == "hold":
                holds[(identifier, index)] = step
    return holds


def _verified_releases(row: dict) -> list[dict]:
    """Return independently verified empty-input release records with causes."""
    candidates = []
    if row.get("event") == "input_released":
        owner = row.get("owner_release", {})
        if (owner.get("verified") and owner.get("keys_down") == [] and
                type(owner.get("verified_ns")) is int):
            candidates.append({"verified_ns": owner["verified_ns"],
                               "reason": owner.get("reason"),
                               "source": "input_released"})
    if row.get("event") == "terminal":
        interruption = row.get("interruption") or {}
        record = interruption.get("record") or {}
        if (record.get("verified") and record.get("keys_down") == [] and
                type(record.get("verified_ns")) is int):
            candidates.append({"verified_ns": record["verified_ns"],
                               "reason": record.get("reason"),
                               "source": "terminal.interruption.record"})
        release = row.get("release") or {}
        if (release.get("verified") and release.get("keys_down") == [] and
                type(release.get("verified_ns")) is int):
            candidates.append({"verified_ns": release["verified_ns"],
                               "reason": release.get("reason"),
                               "source": "terminal.release"})
    return candidates


def reconstruct_holds(events: list[dict]) -> list[dict]:
    """Reconstruct rigorous occupancy bounds for every started hold step.

    Current runtime ordering used by the proof:
    - each key-down InputOwner call emits ``input_admission`` after X11 sync;
    - ``keys_held`` follows all requested key-down acknowledgements;
    - on normal completion, the hold loop captures while keys are down, then the
      ``finally`` block releases all keys, then one final snapshot occurs before
      ``step_completed``;
    - on cancellation, an owner ``verified_ns`` proves empty physical input.

    No normal key-up timestamp is logged, so exact durations are intentionally
    left unknown.
    """
    definitions = submit_steps(events)
    rows: dict[tuple[str, int], dict] = {}
    active: tuple[str, int] | None = None
    cancel_received: dict[str, list[int]] = defaultdict(list)
    terminal_by_id: dict[str, dict] = {}
    early_release_by_id: dict[str, list[dict]] = defaultdict(list)

    for row in events:
        event = row.get("event")
        if event == "command" and row.get("command", {}).get("op") == "cancel":
            cancel_received[row["command"]["id"]].append(row["received_ns"])
        elif event == "input_released":
            early_release_by_id[row["id"]].append(row)
        elif event == "terminal":
            terminal_by_id[row["id"]] = row

        if event == "step_started" and row.get("operation") == "hold":
            key = (row["id"], row["step"])
            if key not in definitions:
                raise AssertionError(f"started hold missing submitted definition: {key}")
            if active is not None:
                raise AssertionError(f"overlapping hold steps: {active} -> {key}")
            active = key
            rows[key] = {
                "id": key[0], "step": key[1], "requested_keys": list(definitions[key]["keys"]),
                "programmed_duration_ms": definitions[key]["duration_ms"],
                "step_started_ns": row["issued_ns"], "admissions": [], "observations": [],
                "keys_held": None, "step_completed_ns": None,
            }
        elif active is not None and event == "input_admission":
            rows[active]["admissions"].append(row)
        elif event == "keys_held":
            key = (row["id"], row["step"])
            if active != key:
                raise AssertionError(f"keys_held outside active hold: {key}, active={active}")
            rows[key]["keys_held"] = row
        elif event == "observation" and (row.get("id"), row.get("step")) in rows:
            rows[(row["id"], row["step"])]["observations"].append(row)
        elif event == "step_completed" and (row.get("id"), row.get("step")) in rows:
            key = (row["id"], row["step"])
            rows[key]["step_completed_ns"] = row["completed_ns"]
            if active == key:
                active = None
        elif event == "terminal" and active is not None and row.get("id") == active[0]:
            active = None

    result = []
    for key in sorted(rows, key=lambda item: rows[item]["step_started_ns"]):
        row = rows[key]
        held = row["keys_held"]
        if held is None:
            raise AssertionError(f"started hold never reached keys_held: {key}")
        admissions = row["admissions"]
        requested = row["requested_keys"]
        if [entry["key"] for entry in admissions] != requested:
            raise AssertionError(
                f"input admissions do not match requested keys for {key}: "
                f"{[entry['key'] for entry in admissions]} != {requested}")
        if sorted(held["keys"]) != sorted(requested):
            raise AssertionError(f"keys_held mismatch for {key}")

        first_admitted = min(entry["admitted_ns"] for entry in admissions)
        first_ack = min(entry["input_ack_ns"] for entry in admissions)
        all_keys_ack = held["input_ack_ns"]
        observations = sorted(row["observations"], key=lambda item: item["capture_ns"])
        terminal = terminal_by_id.get(row["id"])
        if terminal is None:
            raise AssertionError(f"hold program missing terminal: {row['id']}")

        release_candidates = []
        for release in early_release_by_id.get(row["id"], []):
            release_candidates.extend(_verified_releases(release))
        release_candidates.extend(_verified_releases(terminal))

        completed = row["step_completed_ns"] is not None
        proof = None
        if completed:
            # session_v4 hold semantics: observations[:-1] are captured inside
            # the hold loop; observations[-1] is captured after finally releases
            # every key and before step_completed is emitted.
            if not observations:
                raise AssertionError(f"completed hold has no post-release observation: {key}")
            released_by = observations[-1]["capture_ns"]
            in_hold = observations[:-1]
            confirmed_until = max(
                [first_ack] + [sample["capture_ns"] for sample in in_hold]
            )
            proof = "normal: last snapshot is after finally key-up; earlier snapshots are in hold loop"
        else:
            if not release_candidates:
                raise AssertionError(f"interrupted hold has no verified empty release: {key}")
            earliest_release = min(release_candidates, key=lambda item: item["verified_ns"])
            released_by = earliest_release["verified_ns"]
            release_reason = earliest_release.get("reason")
            cancellation_times = [value for value in cancel_received.get(row["id"], []) if value <= released_by]
            if (terminal.get("status") == "cancelled" and release_reason == "cancelled" and
                    cancellation_times):
                # Only a release explicitly attributed to cancellation permits
                # pre-cancel captures to certify continued occupancy. A terminal
                # may be cancelled after an earlier independent focus/expiry
                # release; that case must remain conservative.
                trigger = min(cancellation_times)
                certified = [sample["capture_ns"] for sample in observations
                             if first_ack <= sample["capture_ns"] < trigger]
                confirmed_until = max([first_ack] + certified)
                proof = ("cancelled: earliest verified release cause is cancelled; "
                         "captures before cancel command receipt precede that cause")
            else:
                # Expiry/focus/surface/unknown release can race observations;
                # without a key-up event only the down acknowledgement is
                # universally safe.
                confirmed_until = first_ack
                proof = ("asynchronous/unknown release: no later held sample is "
                         "universally provable")

        if not (first_admitted <= first_ack <= confirmed_until <= released_by):
            raise AssertionError(
                f"invalid occupancy bounds for {key}: "
                f"{first_admitted}, {first_ack}, {confirmed_until}, {released_by}")
        lower = confirmed_until - first_ack
        upper = released_by - first_admitted
        result.append({
            "id": row["id"], "step": row["step"], "requested_keys": requested,
            "programmed_duration_ms": row["programmed_duration_ms"],
            "terminal_status": terminal["status"],
            "first_key_admitted_ns": first_admitted,
            "first_key_ack_ns": first_ack,
            "all_keys_ack_ns": all_keys_ack,
            "confirmed_any_key_held_until_ns": confirmed_until,
            "released_by_ns": released_by,
            "release_reason": (None if completed else release_reason),
            "physical_any_key_occupancy_lower_ms": ms(lower),
            "physical_any_key_occupancy_upper_ms": ms(upper),
            "occupancy_interval_width_ms": ms(upper - lower),
            "exact_physical_duration_known": False,
            "proof": proof,
        })
    return result


def decision_occupancy_bounds(report: dict, holds: list[dict]) -> list[dict]:
    by_id: dict[str, list[dict]] = defaultdict(list)
    for row in holds:
        by_id[row["id"]].append(row)
    out = []
    for decision in report["decisions"]:
        start = decision["controller_model_started_ns"]
        end = decision["controller_model_ended_ns"]
        lower = upper = 0
        used = []
        for identifier in decision["cover_program_ids"]:
            for hold in by_id.get(identifier, []):
                lower += overlap_ns(
                    hold["first_key_ack_ns"], hold["confirmed_any_key_held_until_ns"], start, end)
                upper += overlap_ns(
                    hold["first_key_admitted_ns"], hold["released_by_ns"], start, end)
                used.append(f"{hold['id']}:{hold['step']}")
        out.append({
            "iteration": decision["iteration"],
            "model_wait_ms": ms(end - start),
            "physical_any_key_occupancy_lower_ms": ms(lower),
            "physical_any_key_occupancy_upper_ms": ms(upper),
            "occupancy_interval_width_ms": ms(upper - lower),
            "hold_steps": used,
            "exact_physical_duration_known": False,
        })
    return out


def analyze(run_root: Path) -> dict:
    report_path = run_root / "report.json"
    events_path = run_root / "runtime/events.jsonl"
    report = json.loads(report_path.read_text(encoding="utf-8"))
    events = load_jsonl(events_path)
    holds = reconstruct_holds(events)
    decisions = decision_occupancy_bounds(report, holds)
    return {
        "schema": "map01-held-input-occupancy-posthoc-v1",
        "run": run_root.name,
        "source_sha256": {
            "report.json": sha256(report_path),
            "runtime/events.jsonl": sha256(events_path),
        },
        "holds": holds,
        "decisions": decisions,
        "totals": {
            "physical_any_key_occupancy_lower_ms": round(sum(
                row["physical_any_key_occupancy_lower_ms"] for row in decisions), 3),
            "physical_any_key_occupancy_upper_ms": round(sum(
                row["physical_any_key_occupancy_upper_ms"] for row in decisions), 3),
            "occupancy_interval_width_ms": round(sum(
                row["occupancy_interval_width_ms"] for row in decisions), 3),
            "hold_steps": len(holds),
        },
        "interpretation": (
            "Interval-censored physical any-key occupancy. The retained schema does not "
            "timestamp normal key-up operations, so exact held duration is not identifiable."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("run_root", type=Path)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    value = analyze(args.run_root)
    encoded = json.dumps(value, indent=2) + "\n"
    if args.out:
        if args.out.exists():
            raise FileExistsError(args.out)
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(encoded, encoding="utf-8", newline="\n")
    else:
        print(encoded, end="")


if __name__ == "__main__":
    main()
