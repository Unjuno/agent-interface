"""Interval-censored hold reconstruction including pre-held partial admission."""
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


def _execution_index(events: list[dict]) -> tuple[dict, set]:
    active = None
    rows = {}
    interrupted_before_held = set()
    terminals = {r["id"]: r for r in events if r.get("event") == "terminal"}
    cancels = defaultdict(list)
    for row in events:
        if row.get("event") == "command" and row.get("command", {}).get("op") == "cancel":
            cancels[row["command"]["id"]].append(row["received_ns"])
        event = row.get("event")
        if event == "step_started" and row.get("operation") == "hold":
            if active is not None:
                raise AssertionError(f"overlapping holds: {active} -> {row}")
            active = (row["id"], row["step"])
            rows[active] = {"start": row, "admissions": [], "keys_held": None,
                            "observations": [], "completed": False}
        elif active is not None and event == "input_admission":
            rows[active]["admissions"].append(row)
        elif event == "keys_held":
            key = (row["id"], row["step"])
            if active != key:
                raise AssertionError(f"keys_held outside active hold: {key}")
            rows[key]["keys_held"] = row
        elif event == "observation" and active == (row.get("id"), row.get("step")):
            rows[active]["observations"].append(row)
        elif event == "step_completed" and active == (row.get("id"), row.get("step")):
            rows[active]["completed"] = True
            active = None
        elif event == "terminal" and active is not None and active[0] == row.get("id"):
            key = active
            source, terminal = rows[key], terminals[key[0]]
            if source["keys_held"] is None:
                interruption = (terminal.get("interruption") or {}).get("record") or {}
                release = terminal.get("release") or {}
                cancel_times = [t for t in cancels[key[0]]
                                if t <= interruption.get("verified_ns", -1)]
                if (terminal.get("status") != "cancelled" or
                        terminal.get("steps_completed") != key[1] or
                        interruption.get("reason") != "cancelled" or
                        interruption.get("verified") is not True or
                        interruption.get("keys_down") != [] or
                        interruption.get("buttons_down") != [] or
                        type(interruption.get("verified_ns")) is not int or not cancel_times or
                        release.get("verified") is not True or release.get("keys_down") != [] or
                        release.get("buttons_down") != []):
                    raise AssertionError(f"pre-held interruption lacks verified cancellation: {key}")
                if source["observations"]:
                    raise AssertionError(f"observation during incomplete key acquisition unsupported: {key}")
                requested = held_v1.submit_steps(events)[key]["keys"]
                admitted = [r["key"] for r in source["admissions"]]
                if admitted != requested[:len(admitted)] or len(admitted) > len(requested):
                    raise AssertionError(f"partial admissions are not an ordered request prefix: {key}")
                if any(r["input_ack_ns"] > min(cancel_times) for r in source["admissions"]):
                    raise AssertionError(f"input acknowledgement after cancellation: {key}")
                source["release"] = interruption
                source["cancel_ns"] = min(cancel_times)
                interrupted_before_held.add(key)
            active = None
    if active is not None:
        raise AssertionError(f"stream ended during hold: {active}")
    return rows, interrupted_before_held


def reconstruct_holds(events: list[dict]) -> list[dict]:
    execution, preheld = _execution_index(events)
    if not preheld:
        return held_v1.reconstruct_holds(events)
    filtered = [r for r in events if not (r.get("event") == "step_started" and
                 (r.get("id"), r.get("step")) in preheld)]
    result = held_v1.reconstruct_holds(filtered)
    definitions = held_v1.submit_steps(events)
    terminals = {r["id"]: r for r in events if r.get("event") == "terminal"}
    for key in preheld:
        source, terminal = execution[key], terminals[key[0]]
        requested = list(definitions[key]["keys"])
        admissions = source["admissions"]
        release_ns = source["release"]["verified_ns"]
        if not admissions:
            lower = upper = 0.0
        else:
            first_admitted = min(r["admitted_ns"] for r in admissions)
            first_ack = min(r["input_ack_ns"] for r in admissions)
            lower = 0.0  # no in-hold sample before cancellation
            upper = held_v1.ms(release_ns - first_admitted)
        result.append({
            "id": key[0], "step": key[1], "requested_keys": requested,
            "admitted_keys": [r["key"] for r in admissions],
            "programmed_duration_ms": definitions[key]["duration_ms"],
            "terminal_status": terminal["status"],
            "no_input_before_admission": not admissions,
            "partial_admission_before_keys_held": bool(admissions),
            "first_key_admitted_ns": (min(r["admitted_ns"] for r in admissions)
                                      if admissions else None),
            "first_key_ack_ns": (min(r["input_ack_ns"] for r in admissions)
                                 if admissions else None),
            "all_keys_ack_ns": None, "confirmed_any_key_held_until_ns": None,
            "released_by_ns": release_ns, "release_reason": "cancelled",
            "physical_any_key_occupancy_lower_ms": lower,
            "physical_any_key_occupancy_upper_ms": upper,
            "occupancy_interval_width_ms": held_v1.ms(upper-lower),
            "exact_physical_duration_known": False,
            "proof": ("verified cancel before first admission; zero occupancy" if not admissions
                      else "partial ordered key admissions; no in-hold sample; zero lower bound; verified empty release upper bound"),
        })
    return sorted(result, key=lambda r: execution[(r["id"], r["step"])]["start"]["issued_ns"])


def decision_occupancy_bounds(report: dict, holds: list[dict]) -> list[dict]:
    by_id = defaultdict(list)
    for row in holds:
        by_id[row["id"]].append(row)
    result = []
    for decision in report["decisions"]:
        start, end = decision["controller_model_started_ns"], decision["controller_model_ended_ns"]
        lower = upper = 0
        ids = decision["cover_program_ids"]
        selected = [r for identifier in ids for r in by_id.get(identifier, [])]
        for row in selected:
            if row.get("no_input_before_admission"):
                continue
            first_ack = row["first_key_ack_ns"]
            confirmed = (row["confirmed_any_key_held_until_ns"]
                         if row["confirmed_any_key_held_until_ns"] is not None else first_ack)
            lower += held_v1.overlap_ns(first_ack, confirmed, start, end)
            upper += held_v1.overlap_ns(row["first_key_admitted_ns"], row["released_by_ns"], start, end)
        result.append({"iteration": decision["iteration"], "model_wait_ms": held_v1.ms(end-start),
                       "physical_any_key_occupancy_lower_ms": held_v1.ms(lower),
                       "physical_any_key_occupancy_upper_ms": held_v1.ms(upper),
                       "occupancy_interval_width_ms": held_v1.ms(upper-lower),
                       "hold_steps": [f"{r['id']}:{r['step']}" for r in selected],
                       "exact_physical_duration_known": False})
    return result


def analyze(run_root: Path) -> dict:
    report_path, events_path = run_root / "report.json", run_root / "runtime/events.jsonl"
    report = json.loads(report_path.read_text(encoding="utf-8"))
    events = held_v1.load_jsonl(events_path)
    holds = reconstruct_holds(events)
    decisions = decision_occupancy_bounds(report, holds)
    return {"schema": "map01-held-input-occupancy-fulltrace-v3", "run": run_root.name,
            "source_sha256": {"report.json": sha256(report_path),
                              "runtime/events.jsonl": sha256(events_path)},
            "holds": holds, "decisions": decisions,
            "totals": {"physical_any_key_occupancy_lower_ms": round(sum(
                            r["physical_any_key_occupancy_lower_ms"] for r in decisions), 3),
                       "physical_any_key_occupancy_upper_ms": round(sum(
                            r["physical_any_key_occupancy_upper_ms"] for r in decisions), 3),
                       "occupancy_interval_width_ms": round(sum(
                            r["occupancy_interval_width_ms"] for r in decisions), 3),
                       "hold_steps": len(holds),
                       "no_input_before_admission_steps": sum(r.get("no_input_before_admission", False) for r in holds),
                       "partial_admission_before_keys_held_steps": sum(r.get("partial_admission_before_keys_held", False) for r in holds)},
            "limits": "Exact normal key-up timestamps are absent; this is interval-censored posthoc occupancy, not useful task effect or performance."}


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
