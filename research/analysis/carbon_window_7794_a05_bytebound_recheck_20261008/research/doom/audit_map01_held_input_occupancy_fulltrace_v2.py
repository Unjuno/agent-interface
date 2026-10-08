"""Independent raw-only auditor for fulltrace-v2 occupancy reports."""
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


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def overlap(a: int, b: int, c: int, d: int) -> int:
    return max(0, min(b, d) - max(a, c))


def audit(run_root: Path, output_path: Path) -> dict:
    report_path = run_root / "report.json"
    events_path = run_root / "runtime/events.jsonl"
    report, events, output = read_json(report_path), read_events(events_path), read_json(output_path)
    assert output["schema"] == "map01-held-input-occupancy-fulltrace-v2"
    assert output["source_sha256"] == {"report.json": digest(report_path),
                                        "runtime/events.jsonl": digest(events_path)}
    commands = {r["command"]["id"]: r["command"] for r in events
                if r.get("event") == "command" and r["command"].get("op") == "submit"}
    terminals = {r["id"]: r for r in events if r.get("event") == "terminal"}
    cancel_ns = defaultdict(list)
    for row in events:
        if row.get("event") == "command" and row.get("command", {}).get("op") == "cancel":
            cancel_ns[row["command"]["id"]].append(row["received_ns"])

    raw = {}
    active = None
    early_releases = defaultdict(list)
    for row in events:
        event = row.get("event")
        if event == "step_started" and row.get("operation") == "hold":
            assert active is None
            key = (row["id"], row["step"])
            raw[key] = {"start": row, "admissions": [], "keys_held": None,
                        "observations": [], "completed_ns": None}
            active = key
        elif active is not None and event == "input_admission":
            raw[active]["admissions"].append(row)
        elif event == "keys_held":
            key = (row["id"], row["step"])
            assert active == key
            raw[key]["keys_held"] = row
        elif event == "observation" and (row.get("id"), row.get("step")) in raw:
            raw[(row["id"], row["step"])]["observations"].append(row)
        elif event == "step_completed" and active == (row.get("id"), row.get("step")):
            raw[active]["completed_ns"] = row["completed_ns"]
            active = None
        elif event == "input_released":
            early_releases[row["id"]].append(row)
        elif event == "terminal" and active is not None and active[0] == row.get("id"):
            active = None
    assert active is None
    assert set(raw) == {(r["id"], r["step"]) for r in output["holds"]}
    outputs = {(r["id"], r["step"]): r for r in output["holds"]}
    assert len(outputs) == len(output["holds"])

    for key, source in raw.items():
        row = outputs[key]
        identifier, step = key
        definition = commands[identifier]["steps"][step]
        terminal = terminals[identifier]
        assert definition["op"] == "hold" and row["requested_keys"] == definition["keys"]
        assert row["programmed_duration_ms"] == definition["duration_ms"]
        assert row["terminal_status"] == terminal["status"]
        assert row["exact_physical_duration_known"] is False
        if row.get("no_input_before_admission"):
            interruption = (terminal.get("interruption") or {}).get("record") or {}
            assert source["admissions"] == [] and source["keys_held"] is None
            assert terminal["status"] == "cancelled"
            assert terminal["steps_completed"] == step
            assert interruption.get("reason") == "cancelled"
            assert interruption.get("verified") is True
            assert interruption.get("keys_down") == [] and interruption.get("buttons_down") == []
            assert any(t <= interruption["verified_ns"] for t in cancel_ns[identifier])
            assert row["physical_any_key_occupancy_lower_ms"] == 0
            assert row["physical_any_key_occupancy_upper_ms"] == 0
            assert row["occupancy_interval_width_ms"] == 0
            assert row["released_by_ns"] == interruption["verified_ns"]
            continue

        requested = definition["keys"]
        admitted = source["admissions"]
        assert [r["key"] for r in admitted] == requested
        assert source["keys_held"] is not None
        assert sorted(source["keys_held"]["keys"]) == sorted(requested)
        first_admitted = min(r["admitted_ns"] for r in admitted)
        first_ack = min(r["input_ack_ns"] for r in admitted)
        assert row["first_key_admitted_ns"] == first_admitted
        assert row["first_key_ack_ns"] == first_ack
        observations = sorted(source["observations"], key=lambda r: r["capture_ns"])
        assert observations
        if source["completed_ns"] is not None:
            released_by = observations[-1]["capture_ns"]
            confirmed = max([first_ack] + [r["capture_ns"] for r in observations[:-1]])
            reason = None
        else:
            candidates = []
            for release in early_releases[identifier]:
                owner = release.get("owner_release", {})
                if owner.get("verified") is True and owner.get("keys_down") == []:
                    candidates.append(owner)
            for name in ("interruption", "release"):
                owner = (terminal.get(name) or {}).get("record") if name == "interruption" else terminal.get(name)
                if owner and owner.get("verified") is True and owner.get("keys_down") == []:
                    candidates.append(owner)
            assert candidates
            owner = min(candidates, key=lambda r: r["verified_ns"])
            released_by, reason = owner["verified_ns"], owner.get("reason")
            cancel_before = [t for t in cancel_ns[identifier] if t <= released_by]
            if terminal["status"] == "cancelled" and reason == "cancelled" and cancel_before:
                confirmed = max([first_ack] + [r["capture_ns"] for r in observations
                                               if first_ack <= r["capture_ns"] < min(cancel_before)])
            else:
                confirmed = first_ack
        assert row["confirmed_any_key_held_until_ns"] == confirmed
        assert row["released_by_ns"] == released_by
        assert row["release_reason"] == reason
        lower = (confirmed - first_ack) / 1e6
        upper = (released_by - first_admitted) / 1e6
        assert row["physical_any_key_occupancy_lower_ms"] == round(lower, 3)
        assert row["physical_any_key_occupancy_upper_ms"] == round(upper, 3)
        assert row["occupancy_interval_width_ms"] == round(upper-lower, 3)
        assert 0 <= lower <= upper

    for decision, scored in zip(report["decisions"], output["decisions"], strict=True):
        assert decision["iteration"] == scored["iteration"]
        lo = hi = 0
        identifiers = decision["cover_program_ids"]
        expected_steps = []
        for key, hold in outputs.items():
            if key[0] not in identifiers:
                continue
            expected_steps.append(f"{key[0]}:{key[1]}")
            if hold.get("no_input_before_admission"):
                continue
            lo += overlap(hold["first_key_ack_ns"],
                          hold["confirmed_any_key_held_until_ns"],
                          decision["controller_model_started_ns"],
                          decision["controller_model_ended_ns"])
            hi += overlap(hold["first_key_admitted_ns"], hold["released_by_ns"],
                          decision["controller_model_started_ns"],
                          decision["controller_model_ended_ns"])
        assert scored["hold_steps"] == expected_steps
        assert scored["physical_any_key_occupancy_lower_ms"] == round(lo/1e6, 3)
        assert scored["physical_any_key_occupancy_upper_ms"] == round(hi/1e6, 3)
        assert scored["occupancy_interval_width_ms"] == round((hi-lo)/1e6, 3)

    totals = output["totals"]
    assert totals["hold_steps"] == len(raw)
    assert totals["no_input_before_admission_steps"] == sum(
        bool(row.get("no_input_before_admission")) for row in outputs.values())
    assert totals["physical_any_key_occupancy_lower_ms"] == round(sum(
        row["physical_any_key_occupancy_lower_ms"] for row in output["decisions"]), 3)
    assert totals["physical_any_key_occupancy_upper_ms"] == round(sum(
        row["physical_any_key_occupancy_upper_ms"] for row in output["decisions"]), 3)
    return {"run": run_root.name, "holds": len(raw),
            "no_input_before_admission": totals["no_input_before_admission_steps"],
            "report_sha256": digest(report_path), "events_sha256": digest(events_path),
            "candidate_sha256": digest(output_path), "checks": "PASS"}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()
    names = ("map01-v38-integrated-threat-live-01", "map01-v39-coast-liveness-live-01")
    results = []
    for name, outfile in zip(names, ("v38.json", "v39.json"), strict=True):
        results.append(audit(args.repo / "research/doom/results" / name,
                             args.out_dir / outfile))
    print(json.dumps({"schema": "map01-held-input-occupancy-fulltrace-v2-audit",
                      "runs": results, "errors": []}, indent=2))


if __name__ == "__main__":
    main()
