"""Independent raw-event reconstruction and audit of fulltrace-v3 outputs."""
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
    assert out["schema"] == "map01-held-input-occupancy-fulltrace-v3"
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
            raw[active] = {"start": r, "admissions": [], "keys_held": None,
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
    for key, src in raw.items():
        rid, step = key
        row, term = rows[key], terminals[rid]
        definition = commands[rid]["steps"][step]
        requested = definition["keys"]
        assert definition["op"] == "hold"
        assert row["requested_keys"] == requested
        assert row["programmed_duration_ms"] == definition["duration_ms"]
        assert row["terminal_status"] == term["status"]
        assert row["exact_physical_duration_known"] is False
        admissions = src["admissions"]
        if src["keys_held"] is None:
            interrupt = (term.get("interruption") or {}).get("record") or {}
            assert not src["observations"]
            assert term["status"] == "cancelled" and term["steps_completed"] == step
            assert interrupt.get("verified") is True and interrupt.get("reason") == "cancelled"
            assert interrupt.get("keys_down") == [] and interrupt.get("buttons_down") == []
            cancel_before = [t for t in cancel_times[rid] if t <= interrupt["verified_ns"]]
            assert cancel_before and all(r["input_ack_ns"] <= min(cancel_before) for r in admissions)
            admitted = [r["key"] for r in admissions]
            assert admitted == requested[:len(admitted)] and len(admitted) <= len(requested)
            assert row["admitted_keys"] == admitted
            assert row["no_input_before_admission"] is (len(admissions) == 0)
            assert row["partial_admission_before_keys_held"] is bool(admissions)
            assert row["release_reason"] == "cancelled"
            assert row["released_by_ns"] == interrupt["verified_ns"]
            if admissions:
                first_admitted = min(r["admitted_ns"] for r in admissions)
                first_ack = min(r["input_ack_ns"] for r in admissions)
                upper = (interrupt["verified_ns"] - first_admitted) / 1e6
                assert row["first_key_admitted_ns"] == first_admitted
                assert row["first_key_ack_ns"] == first_ack
                assert row["physical_any_key_occupancy_lower_ms"] == 0.0
                assert row["physical_any_key_occupancy_upper_ms"] == round(upper, 3)
                intervals[key] = (first_ack, first_ack, first_admitted, interrupt["verified_ns"])
            else:
                assert row["physical_any_key_occupancy_lower_ms"] == 0.0
                assert row["physical_any_key_occupancy_upper_ms"] == 0.0
                intervals[key] = None
            assert row["occupancy_interval_width_ms"] == row["physical_any_key_occupancy_upper_ms"]
            continue

        assert [r["key"] for r in admissions] == requested
        assert sorted(src["keys_held"]["keys"]) == sorted(requested)
        first_admitted = min(r["admitted_ns"] for r in admissions)
        first_ack = min(r["input_ack_ns"] for r in admissions)
        assert row["first_key_admitted_ns"] == first_admitted
        assert row["first_key_ack_ns"] == first_ack
        samples = sorted(src["observations"], key=lambda r: r["capture_ns"])
        assert samples
        if src["completed"]:
            release_by = samples[-1]["capture_ns"]
            confirmed = max([first_ack] + [r["capture_ns"] for r in samples[:-1]])
            reason = None
        else:
            candidates = [r for r in releases[rid] if r.get("verified") is True and
                          r.get("keys_down") == []]
            for field in ("interruption", "release"):
                owner = ((term.get(field) or {}).get("record") if field == "interruption"
                         else term.get(field))
                if owner and owner.get("verified") is True and owner.get("keys_down") == []:
                    candidates.append(owner)
            assert candidates
            owner = min(candidates, key=lambda r: r["verified_ns"])
            release_by, reason = owner["verified_ns"], owner.get("reason")
            cancels = [t for t in cancel_times[rid] if t <= release_by]
            if term["status"] == "cancelled" and reason == "cancelled" and cancels:
                confirmed = max([first_ack] + [r["capture_ns"] for r in samples
                                               if first_ack <= r["capture_ns"] < min(cancels)])
            else:
                confirmed = first_ack
        assert row["confirmed_any_key_held_until_ns"] == confirmed
        assert row["released_by_ns"] == release_by and row["release_reason"] == reason
        lo, hi = (confirmed-first_ack)/1e6, (release_by-first_admitted)/1e6
        assert row["physical_any_key_occupancy_lower_ms"] == round(lo, 3)
        assert row["physical_any_key_occupancy_upper_ms"] == round(hi, 3)
        assert row["occupancy_interval_width_ms"] == round(hi-lo, 3)
        assert 0 <= lo <= hi
        intervals[key] = (first_ack, confirmed, first_admitted, release_by)

    for decision, got in zip(report["decisions"], out["decisions"], strict=True):
        selected = [key for identifier in decision["cover_program_ids"]
                    for key in raw if key[0] == identifier]
        assert got["iteration"] == decision["iteration"]
        assert got["hold_steps"] == [f"{k[0]}:{k[1]}" for k in selected]
        lo = hi = 0
        for key in selected:
            interval = intervals[key]
            if interval is not None:
                a, b, c, d = interval
                lo += overlap(a, b, decision["controller_model_started_ns"],
                              decision["controller_model_ended_ns"])
                hi += overlap(c, d, decision["controller_model_started_ns"],
                              decision["controller_model_ended_ns"])
        assert got["physical_any_key_occupancy_lower_ms"] == round(lo/1e6, 3)
        assert got["physical_any_key_occupancy_upper_ms"] == round(hi/1e6, 3)
        assert got["occupancy_interval_width_ms"] == round((hi-lo)/1e6, 3)
    return {"run": run_root.name, "hold_steps": len(rows),
            "no_input_steps": out["totals"]["no_input_before_admission_steps"],
            "partial_admission_steps": out["totals"]["partial_admission_before_keys_held_steps"],
            "source_hashes_match": True, "raw_bounds_reconstructed": True}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()
    names = ("map01-v38-integrated-threat-live-01", "map01-v39-coast-liveness-live-01")
    files = ("v38.json", "v39.json")
    results = [audit(args.repo / "research/doom/results" / name, args.out_dir / file)
               for name, file in zip(names, files, strict=True)]
    print(json.dumps({"schema": "map01-held-input-occupancy-fulltrace-v3-audit",
                      "results": results, "errors": []}, indent=2))


if __name__ == "__main__":
    main()
