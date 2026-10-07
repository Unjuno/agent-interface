"""Early-release bounds with fail-closed handling for later same-hold admissions."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location(
    "frozen_fulltrace_v4", HERE / "dependencies" / "analyze_map01_held_input_occupancy_fulltrace_v4.py")
base = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(base)


def _verified_empty(row: dict) -> dict | None:
    owner = row.get("owner_release", {}) if row.get("event") == "input_released" else row
    if (owner.get("verified") is True and owner.get("keys_down") == [] and
            type(owner.get("verified_ns")) is int):
        return owner
    return None


def reconstruct_holds(events: list[dict]) -> list[dict]:
    holds = base.reconstruct_holds(events)
    by_key = {(r["id"], r["step"]): r for r in holds}
    observations: dict[tuple[str, int], list[dict]] = defaultdict(list)
    admissions: dict[tuple[str, int], list[dict]] = defaultdict(list)
    releases: dict[tuple[str, int], list[dict]] = defaultdict(list)
    terminals = {r["id"]: r for r in events if r.get("event") == "terminal"}
    completed_steps = {(r["id"], r["step"]) for r in events
                       if r.get("event") == "step_completed"}
    cancel_times: dict[str, list[int]] = defaultdict(list)
    for event in events:
        if event.get("event") == "command" and event.get("command", {}).get("op") == "cancel":
            cancel_times[event["command"]["id"]].append(event["received_ns"])
    active = None
    for event in events:
        kind = event.get("event")
        if kind == "step_started" and event.get("operation") == "hold":
            active = (event["id"], event["step"])
        elif active is not None and kind == "input_admission":
            admissions[active].append(event)
        elif active is not None and kind == "observation" and (event.get("id"), event.get("step")) == active:
            observations[active].append(event)
        elif active is not None and kind == "input_released" and event.get("id") == active[0]:
            owner = _verified_empty(event)
            if owner is not None:
                releases[active].append(owner)
        elif kind == "step_completed" and active == (event.get("id"), event.get("step")):
            active = None
        elif kind == "terminal" and active is not None and active[0] == event.get("id"):
            active = None

    for key, row in by_key.items():
        if row.get("terminal_status") is None:
            continue
        # Completion belongs to the individual hold step. A later program
        # cancellation must not hide an already completed hold's early release.
        terminal = terminals[key[0]]
        if key not in completed_steps:
            continue
        samples = sorted(observations[key], key=lambda r: r["capture_ns"])
        if not samples:
            continue
        ordinary_release_by = samples[-1]["capture_ns"]
        first_admitted = row["first_key_admitted_ns"]
        candidates = [r for r in releases[key]
                      if first_admitted <= r["verified_ns"] < ordinary_release_by]
        for name in ("interruption", "release"):
            obj = terminal.get(name) or {}
            owner = obj.get("record", {}) if name == "interruption" else obj
            if (owner.get("verified") is True and owner.get("keys_down") == [] and
                    type(owner.get("verified_ns")) is int and
                    first_admitted <= owner["verified_ns"] < ordinary_release_by):
                candidates.append(owner)
        if not candidates:
            continue
        earliest = min(candidates, key=lambda r: r["verified_ns"])
        release_ns = earliest["verified_ns"]
        if any(r["admitted_ns"] >= release_ns or r["input_ack_ns"] > release_ns
               for r in admissions[key]):
            raise AssertionError(f"a later admission/ack makes one occupancy interval invalid: {key}")
        first_ack = row["first_key_ack_ns"]
        release_reason = earliest.get("reason")
        eligible_cancels = [t for t in cancel_times[key[0]] if t <= release_ns]
        if release_reason == "cancelled" and eligible_cancels:
            trigger_ns = min(eligible_cancels)
            certified = [r["capture_ns"] for r in samples
                         if first_ack <= r["capture_ns"] < min(trigger_ns, release_ns)]
            confirmed = max([first_ack] + certified)
        else:
            # For asynchronous focus/expiry/unknown release, key-up and sync
            # can precede the release record timestamp; earlier captures do
            # not prove continued occupancy.
            confirmed = first_ack
        lower_ms = base.base.held_v1.ms(confirmed - first_ack)
        upper_ms = base.base.held_v1.ms(release_ns - first_admitted)
        if confirmed > release_ns or lower_ms > upper_ms:
            raise AssertionError(f"early-release bounds are inconsistent: {key}")
        row.update({
            "confirmed_any_key_held_until_ns": confirmed,
            "released_by_ns": release_ns,
            "release_reason": release_reason,
            "physical_any_key_occupancy_lower_ms": lower_ms,
            "physical_any_key_occupancy_upper_ms": upper_ms,
            "occupancy_interval_width_ms": base.base.held_v1.ms((release_ns-first_admitted)-(confirmed-first_ack)),
            "proof": "completed step with independently verified empty release before final snapshot; later captures excluded from positive occupancy proof",
        })
    return holds


def analyze(run_root: Path) -> dict:
    report_path, events_path = run_root / "report.json", run_root / "runtime/events.jsonl"
    report = json.loads(report_path.read_text(encoding="utf-8"))
    events = base.base.held_v1.load_jsonl(events_path)
    holds = reconstruct_holds(events)
    decisions = base.base.decision_occupancy_bounds(report, holds)
    return {"schema": "map01-held-input-occupancy-early-release-v2",
            "run": run_root.name,
            "source_sha256": {"report.json": base.sha(report_path), "runtime/events.jsonl": base.sha(events_path)},
            "holds": holds, "decisions": decisions,
            "totals": {"physical_any_key_occupancy_lower_ms": round(sum(r["physical_any_key_occupancy_lower_ms"] for r in decisions), 3),
                       "physical_any_key_occupancy_upper_ms": round(sum(r["physical_any_key_occupancy_upper_ms"] for r in decisions), 3),
                       "occupancy_interval_width_ms": round(sum(r["occupancy_interval_width_ms"] for r in decisions), 3),
                       "hold_steps": len(holds),
                       "no_input_before_admission_steps": sum(r.get("no_input_before_admission", False) for r in holds),
                       "partial_admission_before_keys_held_steps": sum(r.get("partial_admission_before_keys_held", False) for r in holds),
                       "cancel_raced_input_ack_steps": sum(r.get("cancel_raced_input_ack", False) for r in holds)},
            "limits": "Exact normal key-up time is absent; intervals are conservative posthoc bounds, not task-effect or performance results."}


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
