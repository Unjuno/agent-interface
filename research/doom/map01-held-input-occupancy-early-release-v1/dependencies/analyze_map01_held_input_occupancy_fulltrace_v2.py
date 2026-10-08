"""Complete-trace successor for interval-censored MAP01 hold occupancy."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location(
    "held_v1", HERE / "analyze_map01_held_input_occupancy_v1.py")
held_v1 = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(held_v1)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _index_hold_execution(events: list[dict]) -> tuple[dict, set]:
    active = None
    execution = {}
    no_input = set()
    terminals = {row["id"]: row for row in events if row.get("event") == "terminal"}
    cancel_receipts = defaultdict(list)
    for row in events:
        if row.get("event") == "command" and row.get("command", {}).get("op") == "cancel":
            cancel_receipts[row["command"]["id"]].append(row["received_ns"])
        event = row.get("event")
        if event == "step_started" and row.get("operation") == "hold":
            if active is not None:
                raise AssertionError(f"overlapping started holds: {active} -> {row}")
            key = (row["id"], row["step"])
            active = key
            execution[key] = {"start": row, "admissions": [], "keys_held": None}
        elif active is not None and event == "input_admission":
            execution[active]["admissions"].append(row)
        elif event == "keys_held":
            key = (row["id"], row["step"])
            if active != key:
                raise AssertionError(f"keys_held outside active hold: {key}, active={active}")
            execution[key]["keys_held"] = row
        elif event == "step_completed" and active == (row.get("id"), row.get("step")):
            active = None
        elif event == "terminal" and active is not None and active[0] == row.get("id"):
            key = active
            record = execution[key]
            if record["keys_held"] is None:
                if record["admissions"]:
                    raise AssertionError(f"partial/unacknowledged input needs a separate bound: {key}")
                terminal = terminals[row["id"]]
                interruption = (terminal.get("interruption") or {}).get("record") or {}
                release = terminal.get("release") or {}
                cancel_before_release = any(
                    t <= interruption.get("verified_ns", -1)
                    for t in cancel_receipts.get(row["id"], []))
                if (terminal.get("status") != "cancelled" or
                        terminal.get("steps_completed") != key[1] or
                        interruption.get("reason") != "cancelled" or
                        interruption.get("verified") is not True or
                        interruption.get("keys_down") != [] or
                        interruption.get("buttons_down") != [] or
                        type(interruption.get("verified_ns")) is not int or
                        not cancel_before_release or
                        release.get("verified") is not True or
                        release.get("keys_down") != [] or release.get("buttons_down") != []):
                    raise AssertionError(f"unadmitted hold is not proven zero-input cancellation: {key}")
                no_input.add(key)
            active = None
    if active is not None:
        raise AssertionError(f"event stream ended during hold: {active}")
    return execution, no_input


def reconstruct_holds(events: list[dict]) -> list[dict]:
    execution, no_input = _index_hold_execution(events)
    if not no_input:
        return held_v1.reconstruct_holds(events)

    # The frozen v1 parser requires every started hold to reach keys_held.  A
    # proven cancellation before the first key admission is represented here as
    # a zero-occupancy hold, and only its step_started event is omitted from the
    # unchanged v1 reconstruction call. Raw event rows are never modified.
    filtered = [row for row in events if not (
        row.get("event") == "step_started" and
        (row.get("id"), row.get("step")) in no_input)]
    complete = held_v1.reconstruct_holds(filtered)
    definitions = held_v1.submit_steps(events)
    terminals = {row["id"]: row for row in events if row.get("event") == "terminal"}
    for key in no_input:
        start = execution[key]["start"]
        terminal = terminals[key[0]]
        release = terminal["interruption"]["record"]
        complete.append({
            "id": key[0], "step": key[1], "requested_keys": list(definitions[key]["keys"]),
            "programmed_duration_ms": definitions[key]["duration_ms"],
            "terminal_status": terminal["status"],
            "no_input_before_admission": True,
            "first_key_admitted_ns": None, "first_key_ack_ns": None,
            "all_keys_ack_ns": None, "confirmed_any_key_held_until_ns": None,
            "released_by_ns": release["verified_ns"], "release_reason": release["reason"],
            "physical_any_key_occupancy_lower_ms": 0.0,
            "physical_any_key_occupancy_upper_ms": 0.0,
            "occupancy_interval_width_ms": 0.0,
            "exact_physical_duration_known": False,
            "proof": "cancelled before any input_admission; verified empty release",
        })
    return sorted(complete, key=lambda row: execution[(row["id"], row["step"])]["start"]["issued_ns"]
                  if (row["id"], row["step"]) in execution else row["first_key_admitted_ns"])


def decision_occupancy_bounds(report: dict, holds: list[dict]) -> list[dict]:
    by_id = defaultdict(list)
    for row in holds:
        by_id[row["id"]].append(row)
    out = []
    for decision in report["decisions"]:
        start, end = decision["controller_model_started_ns"], decision["controller_model_ended_ns"]
        lower = upper = 0
        for identifier in decision["cover_program_ids"]:
            for hold in by_id.get(identifier, []):
                if hold.get("no_input_before_admission"):
                    continue
                lower += held_v1.overlap_ns(
                    hold["first_key_ack_ns"], hold["confirmed_any_key_held_until_ns"], start, end)
                upper += held_v1.overlap_ns(
                    hold["first_key_admitted_ns"], hold["released_by_ns"], start, end)
        out.append({"iteration": decision["iteration"], "model_wait_ms": held_v1.ms(end-start),
                    "physical_any_key_occupancy_lower_ms": held_v1.ms(lower),
                    "physical_any_key_occupancy_upper_ms": held_v1.ms(upper),
                    "occupancy_interval_width_ms": held_v1.ms(upper-lower),
                    "hold_steps": [f"{row['id']}:{row['step']}"
                                   for identifier in decision["cover_program_ids"]
                                   for row in by_id.get(identifier, [])],
                    "exact_physical_duration_known": False})
    return out


def analyze(run_root: Path) -> dict:
    report_path = run_root / "report.json"
    events_path = run_root / "runtime/events.jsonl"
    report = json.loads(report_path.read_text(encoding="utf-8"))
    events = held_v1.load_jsonl(events_path)
    holds = reconstruct_holds(events)
    decisions = decision_occupancy_bounds(report, holds)
    return {"schema": "map01-held-input-occupancy-fulltrace-v2", "run": run_root.name,
            "source_sha256": {"report.json": sha256(report_path),
                              "runtime/events.jsonl": sha256(events_path)},
            "holds": holds, "decisions": decisions,
            "totals": {"physical_any_key_occupancy_lower_ms": round(sum(
                            row["physical_any_key_occupancy_lower_ms"] for row in decisions), 3),
                       "physical_any_key_occupancy_upper_ms": round(sum(
                            row["physical_any_key_occupancy_upper_ms"] for row in decisions), 3),
                       "occupancy_interval_width_ms": round(sum(
                            row["occupancy_interval_width_ms"] for row in decisions), 3),
                       "hold_steps": len(holds),
                       "no_input_before_admission_steps": sum(
                            row.get("no_input_before_admission", False) for row in holds)},
            "interpretation": "Full retained trace; exact normal key-up duration remains unknown.",
            "scope": "posthoc occupancy bounds only; not useful semantic effect, efficacy, or tempo"}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("run_root", type=Path)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    encoded = json.dumps(analyze(args.run_root), indent=2) + "\n"
    if args.out:
        if args.out.exists():
            raise FileExistsError(args.out)
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(encoded, encoding="utf-8", newline="\n")
    else:
        print(encoded, end="")


if __name__ == "__main__":
    main()
