"""Conservative posthoc bounds for cancel/input-ack races in full traces."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location(
    "fulltrace_v3", HERE / "analyze_map01_held_input_occupancy_fulltrace_v3.py")
base = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(base)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _late_ack_admissions(events: list[dict]) -> tuple[set, dict]:
    active = None
    rows = {}
    cancel_times = defaultdict(list)
    terminals = {r["id"]: r for r in events if r.get("event") == "terminal"}
    for r in events:
        if r.get("event") == "command":
            cmd = r.get("command", {})
            if cmd.get("op") == "cancel":
                cancel_times[cmd["id"]].append(r["received_ns"])
        event = r.get("event")
        if event == "step_started" and r.get("operation") == "hold":
            if active is not None:
                raise AssertionError(f"overlapping hold steps: {active}")
            active = (r["id"], r["step"])
            rows[active] = {"admissions": [], "keys_held": False, "observations": []}
        elif active is not None and event == "input_admission":
            rows[active]["admissions"].append(r)
        elif event == "keys_held":
            key = (r["id"], r["step"])
            if active != key:
                raise AssertionError(f"keys_held outside active hold: {key}")
            rows[key]["keys_held"] = True
        elif event == "observation" and active == (r.get("id"), r.get("step")):
            rows[active]["observations"].append(r)
        elif event == "step_completed" and active == (r.get("id"), r.get("step")):
            active = None
        elif event == "terminal" and active is not None and active[0] == r.get("id"):
            active = None
    if active is not None:
        raise AssertionError(f"trace ended during hold: {active}")

    definitions = base.held_v1.submit_steps(events)
    late = set()
    detail = {}
    for key, record in rows.items():
        if record["keys_held"] or not record["admissions"]:
            continue
        terminal = terminals[key[0]]
        interruption = (terminal.get("interruption") or {}).get("record") or {}
        received = [t for t in cancel_times[key[0]] if t <= interruption.get("verified_ns", -1)]
        if not received or terminal.get("status") != "cancelled":
            continue  # the v3 path applies its stricter fail-closed checks
        cancel_ns = min(received)
        requested = definitions[key]["keys"]
        admitted = [r["key"] for r in record["admissions"]]
        if admitted != requested[:len(admitted)] or len(admitted) > len(requested):
            continue  # leave unsupported data for the v3 fail-closed path
        raced = [r for r in record["admissions"]
                 if r["admitted_ns"] <= cancel_ns < r["input_ack_ns"]]
        if raced:
            late.update(id(r) for r in raced)
            detail[key] = {"admissions": list(record["admissions"]),
                           "cancel_ns": cancel_ns, "terminal": terminal,
                           "release": interruption}
    return late, detail


def reconstruct_holds(events: list[dict]) -> list[dict]:
    late_ids, detail = _late_ack_admissions(events)
    filtered = [r for r in events if id(r) not in late_ids]
    holds = base.reconstruct_holds(filtered)
    by_key = {(r["id"], r["step"]): r for r in holds}
    for key, info in detail.items():
        row = by_key[key]
        admissions = info["admissions"]
        first_admitted = min(r["admitted_ns"] for r in admissions)
        first_ack = min(r["input_ack_ns"] for r in admissions)
        release_ns = info["release"]["verified_ns"]
        if not first_admitted <= info["cancel_ns"] < first_ack <= release_ns:
            raise AssertionError(f"cancel/admission/ack/release order invalid: {key}")
        row.update({
            "requested_keys": list(base.held_v1.submit_steps(events)[key]["keys"]),
            "admitted_keys": [r["key"] for r in admissions],
            "no_input_before_admission": False,
            "partial_admission_before_keys_held": True,
            "cancel_raced_input_ack": True,
            "first_key_admitted_ns": first_admitted,
            "first_key_ack_ns": first_ack,
            "confirmed_any_key_held_until_ns": None,
            "released_by_ns": release_ns,
            "release_reason": "cancelled",
            "physical_any_key_occupancy_lower_ms": 0.0,
            "physical_any_key_occupancy_upper_ms": base.held_v1.ms(release_ns-first_admitted),
            "occupancy_interval_width_ms": base.held_v1.ms(release_ns-first_admitted),
            "proof": "admission timestamp precedes cancel but ack follows it; no in-hold sample, so lower=0 and verified-release upper bound",
        })
    return holds


def analyze(run_root: Path) -> dict:
    report_path, events_path = run_root / "report.json", run_root / "runtime/events.jsonl"
    report = json.loads(report_path.read_text(encoding="utf-8"))
    events = base.held_v1.load_jsonl(events_path)
    holds = reconstruct_holds(events)
    decisions = base.decision_occupancy_bounds(report, holds)
    return {"schema": "map01-held-input-occupancy-fulltrace-v4", "run": run_root.name,
            "source_sha256": {"report.json": sha(report_path), "runtime/events.jsonl": sha(events_path)},
            "holds": holds, "decisions": decisions,
            "totals": {"physical_any_key_occupancy_lower_ms": round(sum(r["physical_any_key_occupancy_lower_ms"] for r in decisions), 3),
                       "physical_any_key_occupancy_upper_ms": round(sum(r["physical_any_key_occupancy_upper_ms"] for r in decisions), 3),
                       "occupancy_interval_width_ms": round(sum(r["occupancy_interval_width_ms"] for r in decisions), 3),
                       "hold_steps": len(holds),
                       "no_input_before_admission_steps": sum(r.get("no_input_before_admission", False) for r in holds),
                       "partial_admission_before_keys_held_steps": sum(r.get("partial_admission_before_keys_held", False) for r in holds),
                       "cancel_raced_input_ack_steps": sum(r.get("cancel_raced_input_ack", False) for r in holds)},
            "limits": "Exact normal key-up time is not present; in-flight admission is interval-censored and is not a semantic effect or performance result."}


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
