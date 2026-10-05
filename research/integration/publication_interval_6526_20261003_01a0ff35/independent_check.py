"""Separate raw reconstruction, no imports from producer/candidate/auditors."""
import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path


def demand(condition, message):
    if not condition:
        raise ValueError(message)


def load(data):
    def unique(items):
        out = {}
        for k, v in items:
            demand(k not in out, "duplicate-key")
            out[k] = v
        return out
    def nonfinite(value):
        raise ValueError("nonfinite:" + value)
    return json.loads(data, object_pairs_hook=unique, parse_constant=nonfinite)


def possibilities(lower, upper, deadline):
    # Existence of two witnesses, rather than treating an endpoint as the event.
    on_time_possible = lower <= deadline
    late_possible = upper > deadline
    return {flag for flag, exists in ((True, on_time_possible), (False, late_possible)) if exists}


def check(inputs, manifest_path, freeze_path, result_path):
    freeze = load(freeze_path.read_bytes())
    manifest_data = manifest_path.read_bytes()
    demand(hashlib.sha256(manifest_data).hexdigest() == freeze["input_manifest_sha256"], "manifest-binding")
    manifest = load(manifest_data)
    demand(manifest["source_commit"] == "332da58a9b6b825c384a142dfb59d7ed2b8b774e", "source")
    by_path = {}
    for file in manifest["files"]:
        path = file["path"]
        demand(path not in by_path and ".." not in Path(path).parts and not Path(path).is_absolute(), "path")
        data = (inputs / path).read_bytes()
        demand(len(data) == file["bytes"] and hashlib.sha256(data).hexdigest() == file["sha256"], "sha256")
        demand(hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest() == file["git_blob"], "blob")
        by_path[path] = data
    demand(len(by_path) == 370, "input-count")
    raw = "research/analysis/observation_intervention_6526_a02_orbstack_20261003/results/formal-a02/raw/"
    trials = load(by_path[raw + "formal-trials.json"])
    events = [load(line) for line in by_path[raw + "app-events.jsonl"].splitlines() if line]
    result = load(result_path.read_bytes())
    original_ids = [t["trial_id"] for t in trials]
    demand(len(original_ids) == len(set(original_ids)) == 180, "trial-identity")
    rows = result["rows"]
    demand([r["trial_id"] for r in rows] == original_ids, "result-identity")
    counts = Counter()
    aggregate = {}
    for trial, row in zip(trials, rows):
        tid = trial["trial_id"]
        starts = [e for e in events if e["kind"] == "trial_start" and e.get("trial_id") == tid]
        actions = [e for e in events if e["kind"] == "action_effect" and e.get("trial_id") == tid]
        demand(len(starts) == len(actions) == 1, "event-identity")
        lower, upper = actions[0]["action_ns"], actions[0]["persisted_ns"]
        deadline = starts[0]["start_ns"] + trial["deadline_ms"] * 1_000_000
        demand(all(type(t) is int and t >= 0 for t in (lower, upper, deadline)) and lower <= upper, "clock")
        possible = possibilities(lower, upper, deadline)
        label = "UNRESOLVED" if len(possible) == 2 else ("CERTIFIED_ON_TIME" if True in possible else "CERTIFIED_LATE")
        demand(row["label"] == label and row["lower_ns"] == lower and row["upper_ns"] == upper
               and row["deadline_ns"] == deadline, "interval-reconstruction")
        demand(row["interval_width_ns"] == upper - lower and row["lower_minus_deadline_ns"] == lower - deadline
               and row["upper_minus_deadline_ns"] == upper - deadline, "derived-times")
        demand(row["historical_endpoint_label"] == ("MISS" if upper > deadline else "ON_TIME"), "historical-label")
        snapshot = load(by_path[raw + f"deadline-{tid}.json"])
        demand(row["snapshot_lag_ns"] == snapshot["snapshot_ns"] - deadline
               and type(row["snapshot_effect_present"]) is bool
               and row["snapshot_effect_present"] == snapshot["effect_present"], "snapshot")
        demand(row["arm"] == trial["arm"] and row["schedule"] == trial["schedule"], "cell-binding")
        payload = load(by_path[raw + f"effect-{tid}.json"])
        demand(type(payload) is dict and set(payload) == {"trial_id", "value"}
               and type(payload["trial_id"]) is str and payload["trial_id"] == tid
               and type(payload["value"]) is str and payload["value"] == trial["expected_value"], "payload")
        cell = trial["schedule"] + "/" + trial["arm"]
        counts[cell, label] += 1
        aggregate.setdefault(cell, []).append(row)
    demand(len(aggregate) == 6, "cell-count")
    for cell, group in aggregate.items():
        c = result["cells"][cell]
        n, late, unknown, ontime = len(group), counts[cell, "CERTIFIED_LATE"], counts[cell, "UNRESOLVED"], counts[cell, "CERTIFIED_ON_TIME"]
        expected = {"n": n, "late": late, "unresolved": unknown, "on_time": ontime,
                    "miss_count_bounds": [late, late + unknown],
                    "historical_endpoint_misses": sum(r["upper_ns"] > r["deadline_ns"] for r in group)}
        demand(n == 30 and c == expected, "cell-bounds")
    demand(result["scientific_disposition"] == "HOLD_AUDIT_TIMING" and result["h_classification"] == "NOT_EVALUATED", "hold")
    oracle = 0
    for lower in range(7):
        for upper in range(lower, 7):
            for deadline in range(7):
                demand(possibilities(lower, upper, deadline) == {t <= deadline for t in range(lower, upper + 1)}, "finite-oracle")
                oracle += 1
    return {"status": "INDEPENDENT_RAW_CHECK_PASS", "source_files": len(by_path), "rows": len(rows),
            "possible_time_fixtures": oracle, "result_sha256": hashlib.sha256(result_path.read_bytes()).hexdigest()}


def main():
    p = argparse.ArgumentParser()
    for name in ("inputs", "manifest", "freeze", "result"):
        p.add_argument(name, type=Path)
    args = p.parse_args()
    print(json.dumps(check(args.inputs, args.manifest, args.freeze, args.result), sort_keys=True))


if __name__ == "__main__":
    main()
