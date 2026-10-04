"""Completed-hold bounds capped by verified early empty-input releases."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import analyze_map01_held_input_occupancy_fulltrace_v4 as v4


def verified_empty_releases(events: list[dict], identifier: str) -> list[dict]:
    """Collect same-program verified empty-input receipts from raw events."""
    releases = []
    for row in events:
        if row.get("event") == "input_released" and row.get("id") == identifier:
            owner = row.get("owner_release") or {}
            if (owner.get("verified") is True and owner.get("keys_down") == [] and
                    type(owner.get("verified_ns")) is int):
                releases.append(owner)
        elif row.get("event") == "terminal" and row.get("id") == identifier:
            interruption = (row.get("interruption") or {}).get("record") or {}
            terminal_release = row.get("release") or {}
            for owner in (interruption, terminal_release):
                if (owner.get("verified") is True and owner.get("keys_down") == [] and
                        type(owner.get("verified_ns")) is int):
                    releases.append(owner)
    return releases


def reconstruct_holds(events: list[dict]) -> list[dict]:
    holds = v4.reconstruct_holds(events)
    for hold in holds:
        if hold.get("terminal_status") != "completed":
            continue
        candidates = [r for r in verified_empty_releases(events, hold["id"])
                      if hold["first_key_ack_ns"] <= r["verified_ns"] < hold["released_by_ns"]]
        if not candidates:
            continue
        earliest = min(candidates, key=lambda r: r["verified_ns"])
        release_ns = earliest["verified_ns"]
        in_hold_captures = sorted(
            row["capture_ns"] for row in events
            if row.get("event") == "observation" and row.get("id") == hold["id"]
            and row.get("step") == hold["step"]
        )[:-1]
        hold["confirmed_any_key_held_until_ns"] = max(
            [hold["first_key_ack_ns"]] + [capture_ns for capture_ns in in_hold_captures
                                          if hold["first_key_ack_ns"] <= capture_ns < release_ns]
        )
        hold["released_by_ns"] = release_ns
        hold["release_reason"] = earliest.get("reason")
        hold["physical_any_key_occupancy_lower_ms"] = v4.base.held_v1.ms(
            hold["confirmed_any_key_held_until_ns"] - hold["first_key_ack_ns"])
        hold["physical_any_key_occupancy_upper_ms"] = v4.base.held_v1.ms(
            release_ns - hold["first_key_admitted_ns"])
        hold["occupancy_interval_width_ms"] = v4.base.held_v1.ms(
            release_ns - hold["first_key_admitted_ns"] -
            (hold["confirmed_any_key_held_until_ns"] - hold["first_key_ack_ns"]))
        hold["proof"] = ("normal with earlier verified empty release: in-hold captures "
                          "after that release do not certify continued occupancy")
    return holds


def analyze(run_root: Path) -> dict:
    report_path = run_root / "report.json"
    events_path = run_root / "runtime/events.jsonl"
    report = json.loads(report_path.read_text(encoding="utf-8"))
    events = v4.base.held_v1.load_jsonl(events_path)
    holds = reconstruct_holds(events)
    decisions = v4.base.decision_occupancy_bounds(report, holds)
    return {
        "schema": "map01-held-input-occupancy-fulltrace-v7",
        "run": run_root.name,
        "source_sha256": {
            "report.json": hashlib.sha256(report_path.read_bytes()).hexdigest(),
            "runtime/events.jsonl": hashlib.sha256(events_path.read_bytes()).hexdigest(),
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
            "no_input_before_admission_steps": sum(
                row.get("no_input_before_admission", False) for row in holds),
            "partial_admission_before_keys_held_steps": sum(
                row.get("partial_admission_before_keys_held", False) for row in holds),
            "cancel_raced_input_ack_steps": sum(
                row.get("cancel_raced_input_ack", False) for row in holds),
        },
        "limits": "Exact normal key-up time is absent; intervals remain descriptive and "
                  "do not establish task effect, performance, or causality.",
    }


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
