"""Read-only retrospective publication bounds; never imports/runs the fixture."""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

A02 = "research/analysis/observation_intervention_6526_a02_orbstack_20261003/"
RAW = A02 + "results/formal-a02/raw/"
A03 = "research/analysis/observation_intervention_6526_a03_deadline_audit_only_20261003/"
SOURCE = "332da58a9b6b825c384a142dfb59d7ed2b8b774e"


class Invalid(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise Invalid(message)


def integer(value, name):
    require(type(value) is int and value >= 0, "invalid-integer:" + name)
    return value


def strict_load(data):
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, "duplicate-json-key:" + key)
            result[key] = value
        return result
    def nonfinite(value):
        raise Invalid("nonfinite-json:" + value)
    return json.loads(data, object_pairs_hook=pairs, parse_constant=nonfinite)


def typed_equal(a, b):
    if type(a) is not type(b):
        return False
    if type(a) is dict:
        return a.keys() == b.keys() and all(typed_equal(a[k], b[k]) for k in a)
    if type(a) is list:
        return len(a) == len(b) and all(typed_equal(x, y) for x, y in zip(a, b))
    return a == b


def classify(lower, upper, deadline):
    for name, value in (("lower", lower), ("upper", upper), ("deadline", deadline)):
        integer(value, name)
    require(lower <= upper, "inverted-publication-interval")
    if upper <= deadline:
        return "CERTIFIED_ON_TIME"
    if lower > deadline:
        return "CERTIFIED_LATE"
    return "UNRESOLVED"


def validate_records(trials, events, deadlines, effects, receipt):
    require(type(trials) is list and len(trials) == 180, "trial-count")
    require(type(events) is list, "events-type")
    require(type(receipt) is dict and type(receipt.get("exit_code")) is int and receipt["exit_code"] == 0,
            "candidate-exit")
    require(type(receipt.get("trial_count")) is int and receipt["trial_count"] == 180, "receipt-count")
    ids = [t.get("trial_id") for t in trials if type(t) is dict]
    expected_ids = {f"b{b:02d}-{s.lower()}-{a.lower()}" for b in range(1, 31)
                    for s in ("SENSITIVE", "STABLE") for a in ("MINIMAL", "SCREENSHOT", "SHAM")}
    require(len(ids) == 180 and all(type(t) is str for t in ids) and set(ids) == expected_ids,
            "trial-identities")
    require(set(deadlines) == expected_ids and set(effects) == expected_ids, "artifact-identities")
    groups = {kind: {} for kind in ("trial_start", "action_schedule", "action_effect", "deadline_observed")}
    starts = []
    previous = -1
    for event in events:
        require(type(event) is dict and type(event.get("kind")) is str, "event-type")
        mono = integer(event.get("mono_ns"), "event.mono_ns")
        require(mono >= previous, "event-clock-order")
        previous = mono
        kind = event["kind"]
        require(kind not in ("screenshot_error",), "retained-observer-error")
        if kind in groups:
            tid = event.get("trial_id")
            require(type(tid) is str and tid in expected_ids and tid not in groups[kind],
                    "duplicate-or-unknown-event:" + kind)
            groups[kind][tid] = event
            if kind == "trial_start":
                starts.append(tid)
    require(starts == ids and all(set(group) == expected_ids for group in groups.values()),
            "event-allocation-or-coverage")
    complete = [e for e in events if e["kind"] == "run_complete"]
    require(len(complete) == 1 and type(complete[0].get("trials")) is int and complete[0]["trials"] == 180,
            "run-complete")
    rows = []
    for trial in trials:
        tid = trial["trial_id"]
        block = integer(trial.get("block"), "block")
        arm, schedule = trial.get("arm"), trial.get("schedule")
        require(block in range(1, 31) and arm in ("MINIMAL", "SCREENSHOT", "SHAM")
                and schedule in ("SENSITIVE", "STABLE"), "cell")
        require(tid == f"b{block:02d}-{schedule.lower()}-{arm.lower()}", "id-cell-binding")
        ms = integer(trial.get("deadline_ms"), "deadline_ms")
        delay = integer(trial.get("action_delay_ms"), "action_delay_ms")
        require(ms == (100 if schedule == "SENSITIVE" else 500) and delay == 90,
                "frozen-design")
        require(trial.get("action_mode") == "save" and type(trial.get("expected_value")) is str
                and trial["expected_value"] == "committed:" + tid, "trial-payload")
        start, armed, action, observed = [groups[k][tid] for k in groups]
        for key in ("block", "arm", "schedule", "deadline_ms", "action_delay_ms"):
            require(typed_equal(start.get(key), trial[key]), "start-binding:" + key)
        origin = integer(start.get("start_ns"), "start_ns")
        scheduled = integer(armed.get("scheduled_ns"), "scheduled_ns")
        require(type(armed.get("delay_ms")) is int and armed["delay_ms"] == delay, "schedule-delay")
        offset = integer(armed.get("arm_delay_ns"), "arm_delay_ns")
        require(scheduled - origin == offset and 0 <= offset <= 5_000_000, "schedule-origin")
        require(start["mono_ns"] >= origin and armed["mono_ns"] >= scheduled, "record-chronology")
        lower = integer(action.get("action_ns"), "action_ns")
        upper = integer(action.get("persisted_ns"), "persisted_ns")
        require(action.get("action") == "button.invoke" and action.get("effect_path") == f"effect-{tid}.json",
                "action-binding")
        require(type(action.get("scheduled_ns")) is int and action["scheduled_ns"] == scheduled,
                "action-schedule")
        require(lower >= scheduled + delay * 1_000_000 and action["mono_ns"] >= upper,
                "action-chronology")
        deadline = origin + ms * 1_000_000
        snapshot = deadlines[tid]
        require(type(snapshot) is dict and snapshot.get("trial_id") == tid, "deadline-identity")
        require(integer(snapshot.get("deadline_ns"), "deadline_ns") == deadline, "deadline-binding")
        sampled = integer(snapshot.get("snapshot_ns"), "snapshot_ns")
        require(sampled >= deadline and observed["mono_ns"] >= sampled, "snapshot-chronology")
        require(set(snapshot) == {"trial_id", "deadline_ns", "snapshot_ns", "effect_present", "effect_payload"},
                "deadline-schema")
        for key, value in snapshot.items():
            require(typed_equal(observed.get(key), value), "deadline-event-binding:" + key)
        expected = {"trial_id": tid, "value": trial["expected_value"]}
        require(typed_equal(effects[tid], expected), "effect-payload")
        present = snapshot["effect_present"]
        require(type(present) is bool and typed_equal(snapshot["effect_payload"], expected if present else None),
                "snapshot-payload")
        label = classify(lower, upper, deadline)
        rows.append({"trial_id": tid, "schedule": schedule, "arm": arm,
                     "lower_ns": lower, "upper_ns": upper, "deadline_ns": deadline,
                     "interval_width_ns": upper - lower, "label": label,
                     "lower_minus_deadline_ns": lower - deadline,
                     "upper_minus_deadline_ns": upper - deadline,
                     "snapshot_lag_ns": sampled - deadline, "snapshot_effect_present": present,
                     "historical_endpoint_label": "ON_TIME" if upper <= deadline else "MISS"})
    counts = Counter((r["schedule"], r["arm"]) for r in rows)
    require(len(counts) == 6 and set(counts.values()) == {30}, "cell-balance")
    return rows


def verify_inputs(root, manifest, freeze):
    data = manifest.read_bytes()
    require(hashlib.sha256(data).hexdigest() == freeze["input_manifest_sha256"], "manifest-sha256")
    metadata = strict_load(data)
    require(metadata["source_commit"] == SOURCE, "source-identity")
    files = metadata["files"]
    require(type(files) is list and len(files) == 370, "input-selection-count")
    selected = {}
    for item in files:
        path = item["path"]
        require(type(path) is str and path.startswith((A02, A03)) and ".." not in Path(path).parts
                and path not in selected and item["mode"] == "100644", "input-path-mode")
        content = (root / path).read_bytes()
        require(len(content) == item["bytes"] and hashlib.sha256(content).hexdigest() == item["sha256"],
                "input-sha256:" + path)
        blob = hashlib.sha1(b"blob " + str(len(content)).encode() + b"\0" + content).hexdigest()
        require(blob == item["git_blob"], "input-git-blob:" + path)
        selected[path] = content
    return selected


def analyze(selected):
    trials = strict_load(selected[RAW + "formal-trials.json"])
    events = [strict_load(line) for line in selected[RAW + "app-events.jsonl"].splitlines() if line]
    ids = [t["trial_id"] for t in trials]
    rows = validate_records(trials, events,
                            {tid: strict_load(selected[RAW + f"deadline-{tid}.json"]) for tid in ids},
                            {tid: strict_load(selected[RAW + f"effect-{tid}.json"]) for tid in ids},
                            strict_load(selected[RAW + "candidate-receipt.json"]))
    cells = {}
    for schedule in ("SENSITIVE", "STABLE"):
        for arm in ("MINIMAL", "SCREENSHOT", "SHAM"):
            group = [r for r in rows if (r["schedule"], r["arm"]) == (schedule, arm)]
            count = Counter(r["label"] for r in group)
            low = count["CERTIFIED_LATE"]
            high = low + count["UNRESOLVED"]
            cells[schedule + "/" + arm] = {"n": len(group), "on_time": count["CERTIFIED_ON_TIME"],
                "late": low, "unresolved": count["UNRESOLVED"], "miss_count_bounds": [low, high],
                "historical_endpoint_misses": sum(r["historical_endpoint_label"] == "MISS" for r in group)}
    return {"schema": "publication-interval-6526-v1", "analysis_status": "VALID_RETAINED_PUBLICATION_BOUNDS",
            "scientific_disposition": "HOLD_AUDIT_TIMING", "h_classification": "NOT_EVALUATED",
            "candidate_invocations": 0, "original_auditor_invocations": 0,
            "trial_count": len(rows), "cells": cells,
            "snapshot_lag_ns": {"min": min(r["snapshot_lag_ns"] for r in rows),
                "max": max(r["snapshot_lag_ns"] for r in rows),
                "positive": sum(r["snapshot_lag_ns"] > 0 for r in rows)},
            "endpoint_not_certified_late_ids": [r["trial_id"] for r in rows
                if r["historical_endpoint_label"] == "MISS" and r["label"] != "CERTIFIED_LATE"],
            "rows": rows}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("inputs", type=Path)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("freeze", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    freeze = strict_load(args.freeze.read_bytes())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    require(not args.output.exists(), "output-already-exists")
    try:
        result = analyze(verify_inputs(args.inputs, args.manifest, freeze))
    except (Invalid, OSError, KeyError, TypeError, json.JSONDecodeError) as exc:
        result = {"analysis_status": "STOP_ANALYSIS_INPUT", "error": str(exc),
                  "scientific_disposition": "HOLD_AUDIT_TIMING", "h_classification": "NOT_EVALUATED"}
        args.output.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(result, sort_keys=True))
        return 2
    args.output.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in result.items() if k != "rows"}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
