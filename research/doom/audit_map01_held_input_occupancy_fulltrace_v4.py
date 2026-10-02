"""Independent raw-only auditor for cancel/input-ack-race occupancy bounds."""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import defaultdict
from pathlib import Path


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def read_events(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def overlap(a: int, b: int, c: int, d: int) -> int:
    return max(0, min(b, d) - max(a, c))


def audit(run_root: Path, output_path: Path) -> dict:
    report_path, events_path = run_root / "report.json", run_root / "runtime/events.jsonl"
    report, events, out = read_json(report_path), read_events(events_path), read_json(output_path)
    assert out["schema"] == "map01-held-input-occupancy-fulltrace-v4"
    assert out["source_sha256"] == {"report.json": sha(report_path),
                                     "runtime/events.jsonl": sha(events_path)}
    commands = {r["command"]["id"]: r["command"] for r in events
                if r.get("event") == "command" and r["command"].get("op") == "submit"}
    terminals = {r["id"]: r for r in events if r.get("event") == "terminal"}
    cancel_times = defaultdict(list)
    for r in events:
        if r.get("event") == "command" and r.get("command", {}).get("op") == "cancel":
            cancel_times[r["command"]["id"]].append(r["received_ns"])

    raw, active = {}, None
    releases = defaultdict(list)
    for r in events:
        event = r.get("event")
        if event == "step_started" and r.get("operation") == "hold":
            assert active is None
            active = (r["id"], r["step"])
            raw[active] = {"admissions": [], "keys_held": None,
                           "observations": [], "completed": False}
        elif active is not None and event == "input_admission":
            raw[active]["admissions"].append(r)
        elif event == "keys_held":
            key = (r["id"], r["step"])
            assert active == key
            raw[key]["keys_held"] = r
        elif event == "observation" and active == (r.get("id"), r.get("step")):
            raw[active]["observations"].append(r)
        elif event == "step_completed" and active == (r.get("id"), r.get("step")):
            raw[active]["completed"] = True
            active = None
        elif event == "input_released":
            releases[r["id"]].append(r.get("owner_release", {}))
        elif event == "terminal" and active is not None and active[0] == r.get("id"):
            active = None
    assert active is None
    rows = {(r["id"], r["step"]): r for r in out["holds"]}
    assert len(rows) == len(out["holds"]) == len(raw)
    intervals = {}
    for key, source in raw.items():
        rid, step = key
        row, terminal = rows[key], terminals[rid]
        definition = commands[rid]["steps"][step]
        requested, admissions = definition["keys"], source["admissions"]
        assert definition["op"] == "hold"
        assert row["requested_keys"] == requested
        assert row["programmed_duration_ms"] == definition["duration_ms"]
        assert row["terminal_status"] == terminal["status"]
        assert row["exact_physical_duration_known"] is False

        if source["keys_held"] is None:
            interruption = (terminal.get("interruption") or {}).get("record") or {}
            assert not source["observations"]
            assert terminal["status"] == "cancelled" and terminal["steps_completed"] == step
            assert interruption.get("verified") is True and interruption.get("reason") == "cancelled"
            assert interruption.get("keys_down") == [] and interruption.get("buttons_down") == []
            cancel_before = [t for t in cancel_times[rid] if t <= interruption["verified_ns"]]
            assert cancel_before
            cancel_ns = min(cancel_before)
            admitted_keys = [r["key"] for r in admissions]
            assert admitted_keys == requested[:len(admitted_keys)]
            assert len(admitted_keys) <= len(requested)
            assert all(r["admitted_ns"] <= cancel_ns for r in admissions)
            raced = any(r["admitted_ns"] <= cancel_ns < r["input_ack_ns"] for r in admissions)
            assert row.get("cancel_raced_input_ack", False) is raced
            assert row["admitted_keys"] == admitted_keys
            assert row["no_input_before_admission"] is (not admissions)
            assert row["partial_admission_before_keys_held"] is bool(admissions)
            assert row["release_reason"] == "cancelled"
            assert row["released_by_ns"] == interruption["verified_ns"]
            if admissions:
                first_admitted = min(r["admitted_ns"] for r in admissions)
                first_ack = min(r["input_ack_ns"] for r in admissions)
                upper = (interruption["verified_ns"] - first_admitted) / 1e6
                assert row["first_key_admitted_ns"] == first_admitted
                assert row["first_key_ack_ns"] == first_ack
                assert row["physical_any_key_occupancy_lower_ms"] == 0.0
                assert row["physical_any_key_occupancy_upper_ms"] == round(upper, 3)
                intervals[key] = (first_ack, first_ack, first_admitted, interruption["verified_ns"])
            else:
                assert row["physical_any_key_occupancy_lower_ms"] == 0.0
                assert row["physical_any_key_occupancy_upper_ms"] == 0.0
                intervals[key] = None
            assert row["occupancy_interval_width_ms"] == row["physical_any_key_occupancy_upper_ms"]
            continue

        assert [r["key"] for r in admissions] == requested
        assert sorted(source["keys_held"]["keys"]) == sorted(requested)
        first_admitted = min(r["admitted_ns"] for r in admissions)
        first_ack = min(r["input_ack_ns"] for r in admissions)
        assert row["first_key_admitted_ns"] == first_admitted
        assert row["first_key_ack_ns"] == first_ack
        samples = sorted(source["observations"], key=lambda r: r["capture_ns"])
        assert samples
        if source["completed"]:
            released_by = samples[-1]["capture_ns"]
            confirmed = max([first_ack] + [r["capture_ns"] for r in samples[:-1]])
            reason = None
        else:
            possible = [r for r in releases[rid] if r.get("verified") is True and r.get("keys_down") == []]
            for name in ("interruption", "release"):
                owner = ((terminal.get(name) or {}).get("record") if name == "interruption"
                         else terminal.get(name))
                if owner and owner.get("verified") is True and owner.get("keys_down") == []:
                    possible.append(owner)
            assert possible
            owner = min(possible, key=lambda r: r["verified_ns"])
            released_by, reason = owner["verified_ns"], owner.get("reason")
            cancel_before = [t for t in cancel_times[rid] if t <= released_by]
            if terminal["status"] == "cancelled" and reason == "cancelled" and cancel_before:
                confirmed = max([first_ack] + [r["capture_ns"] for r in samples
                                               if first_ack <= r["capture_ns"] < min(cancel_before)])
            else:
                confirmed = first_ack
        assert row["confirmed_any_key_held_until_ns"] == confirmed
        assert row["released_by_ns"] == released_by and row["release_reason"] == reason
        lower, upper = (confirmed-first_ack)/1e6, (released_by-first_admitted)/1e6
        assert row["physical_any_key_occupancy_lower_ms"] == round(lower, 3)
        assert row["physical_any_key_occupancy_upper_ms"] == round(upper, 3)
        assert row["occupancy_interval_width_ms"] == round(upper-lower, 3)
        assert 0 <= lower <= upper
        intervals[key] = (first_ack, confirmed, first_admitted, released_by)

    for decision, got in zip(report["decisions"], out["decisions"], strict=True):
        selected = [key for identifier in decision["cover_program_ids"]
                    for key in raw if key[0] == identifier]
        assert got["iteration"] == decision["iteration"]
        assert got["hold_steps"] == [f"{key[0]}:{key[1]}" for key in selected]
        lo = hi = 0
        for key in selected:
            span = intervals[key]
            if span is not None:
                a, b, c, d = span
                lo += overlap(a, b, decision["controller_model_started_ns"],
                              decision["controller_model_ended_ns"])
                hi += overlap(c, d, decision["controller_model_started_ns"],
                              decision["controller_model_ended_ns"])
        assert got["physical_any_key_occupancy_lower_ms"] == round(lo/1e6, 3)
        assert got["physical_any_key_occupancy_upper_ms"] == round(hi/1e6, 3)
        assert got["occupancy_interval_width_ms"] == round((hi-lo)/1e6, 3)
    totals = out["totals"]
    assert totals["hold_steps"] == len(raw)
    assert totals["no_input_before_admission_steps"] == sum(r["no_input_before_admission"] for r in rows.values())
    assert totals["partial_admission_before_keys_held_steps"] == sum(r["partial_admission_before_keys_held"] for r in rows.values())
    assert totals["cancel_raced_input_ack_steps"] == sum(r.get("cancel_raced_input_ack", False) for r in rows.values())
    return {"run": run_root.name, "hold_steps": len(rows),
            "no_input_steps": totals["no_input_before_admission_steps"],
            "partial_admission_steps": totals["partial_admission_before_keys_held_steps"],
            "cancel_races": totals["cancel_raced_input_ack_steps"],
            "raw_reconstruction": "PASS", "errors": []}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()
    names = ("map01-v38-integrated-threat-live-01", "map01-v39-coast-liveness-live-01")
    files = ("v38.json", "v39.json")
    results = [audit(args.repo / "research/doom/results" / name, args.out_dir / filename)
               for name, filename in zip(names, files, strict=True)]
    print(json.dumps({"schema": "map01-held-input-occupancy-fulltrace-v4-audit",
                      "results": results, "errors": []}, indent=2))


if __name__ == "__main__":
    main()
