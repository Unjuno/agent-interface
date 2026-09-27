"""Interval-censored any-key occupancy with explicit pre-keys_held interruption states.

Successor to analyze_map01_held_input_occupancy_v1.py. This version changes only
hold steps that terminate before `keys_held`. Completed holds and interruptions
after `keys_held` keep the inherited v1 proof rules.
"""
from __future__ import annotations

import argparse, hashlib, json
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
    holds = {}
    for row in events:
        command = row.get("command", {})
        if row.get("event") != "command" or command.get("op") != "submit":
            continue
        for index, step in enumerate(command.get("steps", [])):
            if step.get("op") == "hold":
                holds[(command["id"], index)] = step
    return holds


def _verified_releases(row: dict) -> list[dict]:
    candidates = []
    if row.get("event") == "input_released":
        owner = row.get("owner_release", {})
        if owner.get("verified") is True and owner.get("keys_down") == [] and type(owner.get("verified_ns")) is int:
            candidates.append({"verified_ns": owner["verified_ns"], "reason": owner.get("reason"), "source": "input_released"})
    if row.get("event") == "terminal":
        interruption = row.get("interruption") or {}
        record = interruption.get("record") or {}
        if record.get("verified") is True and record.get("keys_down") == [] and type(record.get("verified_ns")) is int:
            candidates.append({"verified_ns": record["verified_ns"], "reason": record.get("reason"), "source": "terminal.interruption.record"})
        release = row.get("release") or {}
        if release.get("verified") is True and release.get("keys_down") == [] and type(release.get("verified_ns")) is int:
            candidates.append({"verified_ns": release["verified_ns"], "reason": release.get("reason"), "source": "terminal.release"})
    return candidates


def reconstruct_holds(events: list[dict]) -> list[dict]:
    definitions = submit_steps(events)
    rows = {}
    active = None
    cancel_received = defaultdict(list)
    terminal_by_id = {}
    early_release_by_id = defaultdict(list)

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
        admissions = row["admissions"]
        requested = row["requested_keys"]
        admitted_keys = [entry["key"] for entry in admissions]
        if admitted_keys != requested[:len(admitted_keys)] or len(admitted_keys) > len(requested):
            raise AssertionError(f"input admissions are not a requested-key prefix for {key}: {admitted_keys} vs {requested}")

        held = row["keys_held"]
        completed = row["step_completed_ns"] is not None
        terminal = terminal_by_id.get(row["id"])
        if terminal is None:
            raise AssertionError(f"hold program missing terminal: {row['id']}")
        observations = sorted(row["observations"], key=lambda item: item["capture_ns"])

        release_candidates = []
        for release in early_release_by_id.get(row["id"], []):
            release_candidates.extend(_verified_releases(release))
        release_candidates.extend(_verified_releases(terminal))

        if held is None:
            if completed:
                raise AssertionError(f"completed hold never reached keys_held: {key}")
            if not release_candidates:
                raise AssertionError(f"pre-marker interrupted hold has no verified empty release: {key}")
            earliest_release = min(release_candidates, key=lambda item: item["verified_ns"])
            released_by = earliest_release["verified_ns"]
            if not admissions:
                result.append({
                    "id": row["id"], "step": row["step"], "requested_keys": requested,
                    "programmed_duration_ms": row["programmed_duration_ms"],
                    "terminal_status": terminal["status"], "admission_state": "zero_admission",
                    "classification": "zero_admission_interrupted",
                    "admitted_keys": [], "admission_count": 0,
                    "first_key_admitted_ns": None, "first_key_ack_ns": None, "all_keys_ack_ns": None,
                    "confirmed_any_key_held_until_ns": None, "released_by_ns": released_by,
                    "release_reason": earliest_release.get("reason"),
                    "physical_any_key_occupancy_lower_ms": 0.0,
                    "physical_any_key_occupancy_upper_ms": 0.0,
                    "occupancy_interval_width_ms": 0.0,
                    "exact_physical_duration_known": True,
                    "full_keyset_established": False,
                    "proof": "no input_admission record before independently verified empty termination; task-key occupancy is zero under retained runtime event contract",
                })
                continue
            first_admitted = min(entry["admitted_ns"] for entry in admissions)
            first_ack = min(entry["input_ack_ns"] for entry in admissions)
            if not (row["step_started_ns"] <= first_admitted <= first_ack <= released_by):
                raise AssertionError(f"invalid pre-marker interruption order for {key}")
            upper = released_by - first_admitted
            state = "partial_admission" if len(admissions) < len(requested) else "full_admission_no_marker"
            result.append({
                "id": row["id"], "step": row["step"], "requested_keys": requested,
                "programmed_duration_ms": row["programmed_duration_ms"],
                "terminal_status": terminal["status"], "admission_state": state,
                "classification": f"{state}_interrupted",
                "admitted_keys": admitted_keys, "admission_count": len(admissions),
                "first_key_admitted_ns": first_admitted, "first_key_ack_ns": first_ack,
                "all_keys_ack_ns": (max(e["input_ack_ns"] for e in admissions) if len(admissions) == len(requested) else None),
                "confirmed_any_key_held_until_ns": first_ack,
                "released_by_ns": released_by, "release_reason": earliest_release.get("reason"),
                "physical_any_key_occupancy_lower_ms": 0.0,
                "physical_any_key_occupancy_upper_ms": ms(upper),
                "occupancy_interval_width_ms": ms(upper),
                "exact_physical_duration_known": False,
                "full_keyset_established": False,
                "proof": "pre-keys_held interruption: at least one admission may have produced input, but no positive-duration held interval or full-keyset establishment is proven; verified empty release bounds the upper envelope",
            })
            continue

        if admitted_keys != requested:
            raise AssertionError(f"input admissions do not match requested keys for {key}: {admitted_keys} != {requested}")
        if sorted(held["keys"]) != sorted(requested):
            raise AssertionError(f"keys_held mismatch for {key}")
        first_admitted = min(entry["admitted_ns"] for entry in admissions)
        first_ack = min(entry["input_ack_ns"] for entry in admissions)
        all_keys_ack = held["input_ack_ns"]

        if completed:
            if not observations:
                raise AssertionError(f"completed hold has no post-release observation: {key}")
            released_by = observations[-1]["capture_ns"]
            in_hold = observations[:-1]
            confirmed_until = max([first_ack] + [sample["capture_ns"] for sample in in_hold])
            proof = "normal: inherited v1 semantics; last snapshot follows finally key-up"
            release_reason = None
            classification = "ordinary_completed_bounded"
        else:
            if not release_candidates:
                raise AssertionError(f"interrupted hold has no verified empty release: {key}")
            earliest_release = min(release_candidates, key=lambda item: item["verified_ns"])
            released_by = earliest_release["verified_ns"]
            release_reason = earliest_release.get("reason")
            cancellation_times = [value for value in cancel_received.get(row["id"], []) if value <= released_by]
            if terminal.get("status") == "cancelled" and release_reason == "cancelled" and cancellation_times:
                trigger = min(cancellation_times)
                certified = [sample["capture_ns"] for sample in observations if first_ack <= sample["capture_ns"] < trigger]
                confirmed_until = max([first_ack] + certified)
                proof = "cancelled after keys_held: inherited v1 cancellation proof"
            else:
                confirmed_until = first_ack
                proof = "asynchronous/unknown release after keys_held: inherited v1 conservative proof"
            classification = "keys_held_interrupted"

        if not (first_admitted <= first_ack <= confirmed_until <= released_by):
            raise AssertionError(f"invalid occupancy bounds for {key}")
        lower = confirmed_until - first_ack
        upper = released_by - first_admitted
        result.append({
            "id": row["id"], "step": row["step"], "requested_keys": requested,
            "programmed_duration_ms": row["programmed_duration_ms"], "terminal_status": terminal["status"],
            "admission_state": "keys_held", "classification": classification,
            "admitted_keys": admitted_keys, "admission_count": len(admissions),
            "first_key_admitted_ns": first_admitted, "first_key_ack_ns": first_ack,
            "all_keys_ack_ns": all_keys_ack, "confirmed_any_key_held_until_ns": confirmed_until,
            "released_by_ns": released_by, "release_reason": release_reason,
            "physical_any_key_occupancy_lower_ms": ms(lower),
            "physical_any_key_occupancy_upper_ms": ms(upper),
            "occupancy_interval_width_ms": ms(upper - lower),
            "exact_physical_duration_known": False,
            "full_keyset_established": True,
            "proof": proof,
        })

    if len(result) != len(rows):
        raise AssertionError(f"not every started hold classified: {len(result)} != {len(rows)}")
    return result


def decision_occupancy_bounds(report: dict, holds: list[dict]) -> list[dict]:
    by_id = defaultdict(list)
    for row in holds:
        by_id[row["id"]].append(row)
    out = []
    for decision in report["decisions"]:
        start, end = decision["controller_model_started_ns"], decision["controller_model_ended_ns"]
        lower = upper = 0
        used = []
        for identifier in decision["cover_program_ids"]:
            for hold in by_id.get(identifier, []):
                if hold["admission_count"] == 0:
                    used.append(f"{hold['id']}:{hold['step']}")
                    continue
                if hold["classification"] not in ("partial_admission_interrupted", "full_admission_no_marker_interrupted"):
                    lower += overlap_ns(hold["first_key_ack_ns"], hold["confirmed_any_key_held_until_ns"], start, end)
                upper += overlap_ns(hold["first_key_admitted_ns"], hold["released_by_ns"], start, end)
                used.append(f"{hold['id']}:{hold['step']}")
        out.append({
            "iteration": decision["iteration"], "model_wait_ms": ms(end-start),
            "physical_any_key_occupancy_lower_ms": ms(lower),
            "physical_any_key_occupancy_upper_ms": ms(upper),
            "occupancy_interval_width_ms": ms(upper-lower), "hold_steps": used,
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
        "schema": "map01-held-input-occupancy-posthoc-v2",
        "run": run_root.name,
        "source_sha256": {"report.json": sha256(report_path), "runtime/events.jsonl": sha256(events_path)},
        "holds": holds, "decisions": decisions,
        "totals": {
            "physical_any_key_occupancy_lower_ms": round(sum(r["physical_any_key_occupancy_lower_ms"] for r in decisions),3),
            "physical_any_key_occupancy_upper_ms": round(sum(r["physical_any_key_occupancy_upper_ms"] for r in decisions),3),
            "occupancy_interval_width_ms": round(sum(r["occupancy_interval_width_ms"] for r in decisions),3),
            "hold_steps": len(holds),
            "class_counts": dict(sorted(__import__('collections').Counter(r["classification"] for r in holds).items())),
        },
        "interpretation": "Interval-censored physical any-key occupancy. Pre-keys_held interruptions are explicit and never imply full-keyset establishment. Normal key-up remains un-timestamped.",
    }


def main():
    p=argparse.ArgumentParser(); p.add_argument('run_root',type=Path); p.add_argument('--out',type=Path); a=p.parse_args()
    v=analyze(a.run_root); s=json.dumps(v,indent=2)+"\n"
    if a.out:
        if a.out.exists(): raise FileExistsError(a.out)
        a.out.parent.mkdir(parents=True,exist_ok=True); a.out.write_text(s,encoding='utf-8',newline='\n')
    else: print(s,end='')
if __name__=='__main__': main()
