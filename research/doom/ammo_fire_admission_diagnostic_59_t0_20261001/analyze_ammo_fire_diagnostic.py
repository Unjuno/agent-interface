"""Descriptive ammo-HUD / declared-space-hold diagnostic for retained MAP01 logs."""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import defaultdict
from pathlib import Path


def _ammo(row):
    signal = (row.get("signals") or {}).get("ammo") or {}
    value = signal.get("value")
    if signal.get("status") != "observed" or type(value) is not int or value < 0:
        return None
    return value


def analyze_events(events: list[dict], run_name: str = "fixture") -> dict:
    """Join each started declared-space hold to exact source and in-loop HUD rows."""
    definitions = {}
    typed = []
    observations = defaultdict(list)
    started = []
    active = None
    admissions = defaultdict(list)
    held_markers = {}
    completed = {}
    terminals = {}

    for row in events:
        event = row.get("event")
        if event == "command" and (row.get("command") or {}).get("op") == "submit":
            command = row["command"]
            for step_index, step in enumerate(command.get("steps", [])):
                if step.get("op") == "hold":
                    definitions[(command["id"], step_index)] = {
                        "requested_keys": step.get("keys", []),
                        "expected_sequence": command.get("expected_sequence"),
                        "duration_ms": step.get("duration_ms"),
                    }
        elif event == "typed_observation":
            typed.append(row)
        elif event == "observation":
            observations[(row.get("id"), row.get("step"))].append(row)
        elif event == "step_started" and row.get("operation") == "hold":
            key = (row.get("id"), row.get("step"))
            definition = definitions.get(key)
            if definition is None:
                raise ValueError(f"started hold lacks submitted definition: {key}")
            if active is not None:
                raise ValueError(f"overlapping hold events: {active} then {key}")
            active = key
            if "space" in definition["requested_keys"]:
                started.append({
                    "id": key[0], "step": key[1],
                    "requested_keys": list(definition["requested_keys"]),
                    "source_expected_sequence": definition["expected_sequence"],
                    "programmed_duration_ms": definition["duration_ms"],
                    "step_started_ns": row.get("issued_ns"),
                })
        elif event == "input_admission" and active is not None:
            admissions[active].append(row)
        elif event == "keys_held":
            key = (row.get("id"), row.get("step"))
            if active != key:
                raise ValueError(f"keys_held outside active hold: {key}")
            held_markers[key] = row
        elif event == "step_completed":
            key = (row.get("id"), row.get("step"))
            if key in definitions:
                completed[key] = row.get("completed_ns")
            if active == key:
                active = None
        elif event == "terminal":
            terminals[row.get("id")] = row
            if active is not None and active[0] == row.get("id"):
                active = None

    typed_by_locator = defaultdict(list)
    for row in typed:
        typed_by_locator[(row.get("sequence"), row.get("capture_ns"))].append(row)

    result_rows = []
    for item in started:
        key = (item["id"], item["step"])
        requested = item["requested_keys"]
        admitted_keys = [row.get("key") for row in admissions[key]]
        marker = held_markers.get(key)
        exact_admissions = admitted_keys == requested
        exact_marker = marker is not None and sorted(marker.get("keys", [])) == sorted(requested)
        if marker is not None and not exact_marker:
            raise ValueError(f"keys_held keyset mismatch for {key}")
        if marker is not None and not exact_admissions:
            raise ValueError(f"admission sequence mismatch for {key}: {admitted_keys!r}")

        if marker is not None and exact_marker and exact_admissions:
            if key in completed:
                status = "completed_keyset_confirmed"
            else:
                status = "interrupted_after_keyset"
        else:
            status = "partial_or_unconfirmed_no_keyset_marker"

        start_ns = item["step_started_ns"]
        prior = [row for row in typed if type(row.get("capture_ns")) is int
                 and row["capture_ns"] <= start_ns]
        source = max(prior, key=lambda row: row["capture_ns"]) if prior else None
        source_value = _ammo(source) if source else None
        source_status = ("no_pre_step_typed_ammo" if source is None else
                         "observed" if source_value is not None else "pre_step_ammo_unknown")
        source_signal = ((source.get("signals") or {}).get("ammo") or {}) if source else {}

        in_loop_values = []
        if status == "completed_keyset_confirmed":
            step_observations = sorted(observations[key], key=lambda row: row.get("capture_ns", -1))
            if not step_observations:
                raise ValueError(f"completed hold missing post-release observation: {key}")
            if step_observations[-1].get("capture_ns", start_ns) >= completed[key]:
                raise ValueError(f"post-release observation is not before step completion: {key}")
            for observation in step_observations[:-1]:
                if observation.get("capture_ns", -1) < marker.get("input_ack_ns", start_ns):
                    raise ValueError(f"in-loop observation predates full keyset acknowledgement: {key}")
                locator = (observation.get("sequence"), observation.get("capture_ns"))
                matches = typed_by_locator.get(locator, [])
                if len(matches) != 1:
                    raise ValueError(f"typed observation join not unique for {key}: {locator}")
                value = _ammo(matches[0])
                if value is not None:
                    in_loop_values.append(value)

        decreased = (None if status != "completed_keyset_confirmed" or source_value is None
                     else any(value < source_value for value in in_loop_values))
        terminal = terminals.get(item["id"], {})
        result_rows.append({
            **item,
            "status": status,
            "admitted_keys": admitted_keys,
            "keys_held": list(marker.get("keys", [])) if marker else None,
            "terminal_status": terminal.get("status"),
            "source_sequence": source.get("sequence") if source else None,
            "source_ammo": source_value,
            "source_status": source_status,
            "source_sample_age_ms": (round((start_ns - source["capture_ns"]) / 1e6, 3)
                                      if source else None),
            "source_ammo_binding": source_signal.get("binding"),
            "in_loop_ammo_values": in_loop_values,
            "ammo_decreased_in_loop": decreased,
        })

    completed_rows = [row for row in result_rows if row["status"] == "completed_keyset_confirmed"]
    decreased_count = sum(row["ammo_decreased_in_loop"] is True for row in completed_rows)
    completed_missing_source = sum(row["source_ammo"] is None for row in completed_rows)
    completed_missing_samples = sum(not row["in_loop_ammo_values"] for row in completed_rows)
    return {
        "run": run_name,
        "counts": {
            "space_steps_started": len(result_rows),
            "completed_keyset_confirmed": len(completed_rows),
            "interrupted_after_keyset": sum(row["status"] == "interrupted_after_keyset" for row in result_rows),
            "partial_or_unconfirmed_no_keyset_marker": sum(
                row["status"] == "partial_or_unconfirmed_no_keyset_marker" for row in result_rows),
            "source_ammo_unknown": sum(row["source_ammo"] is None for row in result_rows),
            "source_ammo_zero": sum(row["source_ammo"] == 0 for row in result_rows),
            "completed_with_in_loop_ammo_decrease": decreased_count,
            "completed_missing_source_ammo": completed_missing_source,
            "completed_missing_in_loop_ammo_sample": completed_missing_samples,
        },
        "completed_decrease_fraction": (decreased_count / len(completed_rows) if completed_rows else None),
        "space_steps": result_rows,
    }


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    root = args.repo_root.resolve()
    package = Path(__file__).resolve().parent
    freeze = json.loads((package / "FREEZE.json").read_text())
    frozen_sources = {
        "analysis_source_sha256": package / "analyze_ammo_fire_diagnostic.py",
        "auditor_source_sha256": package / "audit_ammo_fire_diagnostic.py",
        "test_source_sha256": package / "test_ammo_fire_diagnostic.py",
        "plan_sha256": package / "PLAN.md",
    }
    for field, path in frozen_sources.items():
        if sha256(path) != freeze[field]:
            raise SystemExit(f"STOP_FROZEN_SOURCE_HASH_MISMATCH:{field}")
    runs = []
    for name, inputs in freeze["inputs"].items():
        event_path, report_path = root / inputs["events"], root / inputs["report"]
        event_hash, report_hash = sha256(event_path), sha256(report_path)
        if event_hash != inputs["events_sha256"] or report_hash != inputs["report_sha256"]:
            raise SystemExit(f"STOP_INPUT_HASH_MISMATCH:{name}")
        events = [json.loads(line) for line in event_path.read_text(encoding="utf-8").splitlines()]
        report = json.loads(report_path.read_text(encoding="utf-8"))
        run = analyze_events(events, name)
        run.update({"events_sha256": event_hash, "report_sha256": report_hash,
                    "post_control_score": report.get("post_control_score")})
        runs.append(run)

    by_name = {run["run"]: run for run in runs}
    v38 = by_name["map01-v38-integrated-threat-live-01"]
    v39 = by_name["map01-v39-coast-liveness-live-01"]
    integrity_ok = all(run["counts"]["completed_missing_source_ammo"] == 0 and
                       run["counts"]["completed_missing_in_loop_ammo_sample"] == 0
                       for run in runs)
    all_completed_positive = all(row["source_ammo"] is not None and row["source_ammo"] > 0
                                  for run in runs for row in run["space_steps"]
                                  if row["status"] == "completed_keyset_confirmed")
    supported = (integrity_ok and all_completed_positive and
                 v39["completed_decrease_fraction"] is not None and
                 v38["completed_decrease_fraction"] is not None and
                 v39["completed_decrease_fraction"] > v38["completed_decrease_fraction"])
    result = {
        "schema": "map01-ammo-fire-diagnostic-v1",
        "allocation": freeze["allocation"],
        "base_main": freeze["base_main"],
        "decision": ("FAIL_INTEGRITY" if not integrity_ok else
                     "PASS_DIAGNOSTIC_CONTRAST_SCOPED" if supported else "HYPOTHESIS_NOT_SUPPORTED"),
        "measurement_integrity_ok": integrity_ok,
        "hypothesis_supported": supported,
        "runs": runs,
        "scope_limits": [
            "two unmatched stochastic retained episodes; descriptive contrast only",
            "ammo decreases temporally inside a declared space hold do not prove which shot caused the HUD change",
            "no target hit, tactical appropriateness, survival benefit, completion, speed, or human-tempo claim",
            "interrupted and partial/unconfirmed holds are excluded from the completed-step fraction",
        ],
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"decision": result["decision"], "hypothesis_supported": supported,
                      "runs": [{"run": run["run"], **run["counts"],
                                "completed_decrease_fraction": run["completed_decrease_fraction"]}
                               for run in runs]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
