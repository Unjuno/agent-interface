#!/usr/bin/env python3
"""Re-audit PNG evidence, then summarize paired runs without an LLM/token proxy."""

import argparse
import csv
import hashlib
import json
from collections import defaultdict
from pathlib import Path

import numpy as np
from PIL import Image


def read_json(path):
    return json.loads(path.read_text())


def jsonl(path):
    return [json.loads(line) for line in path.read_text().splitlines() if line]


def quantiles(values):
    values = [x for x in values if x is not None]
    return {"n": len(values), **{f"p{p}": float(np.quantile(values, p / 100)) if values else None
                                for p in (50, 95, 99)}}


def audit_run(root, run):
    observations = jsonl(root / "observations.jsonl")
    cached = {}
    last = None
    base_sequence = 0
    exact_repeats = 0
    forwarded = 0
    for index, row in enumerate(observations, 1):
        if row["sha256"] not in cached:
            with Image.open(root / "frames" / (row["sha256"] + ".png")) as im:
                im.load()
                raw = im.tobytes()
                geometry = (im.width, im.height, im.mode)
            signature = f"{geometry[0]},{geometry[1]},{geometry[2]}:".encode()
            if hashlib.sha256(signature + raw).hexdigest() != row["sha256"]:
                raise ValueError(f"Archive hash mismatch: {root}, {index}")
            cached[row["sha256"]] = (geometry, np.frombuffer(raw, dtype=np.uint8))
        geometry, pixels = cached[row["sha256"]]
        if geometry != (row["width"], row["height"], row["mode"]) or row["sequence"] != index:
            raise ValueError("Frame metadata or sequence mismatch")
        equal = last is not None and geometry == last[0] and np.array_equal(pixels, last[1])
        exact_repeats += bool(equal)
        expected_suppression = bool(equal and run["strategy"] == "O1")
        if row["exact_unchanged"] != bool(equal) or row["suppressed"] != expected_suppression:
            raise ValueError("Recorded exact equality / gate decision does not match PNG evidence")
        if row["suppressed"]:
            if row["base_sequence"] != base_sequence:
                raise ValueError("Missing receiver image base")
        else:
            forwarded += 1
            base_sequence = index
            if row["base_sequence"] != index:
                raise ValueError("Invalid full-frame reference")
        last = (geometry, pixels)
    if (len(observations) != run["candidate_observations"] or forwarded != run["model_visible_observations"]
            or exact_repeats != run["exact_repeat_opportunities"]
            or run["suppressed_observations"] != len(observations) - forwarded):
        raise ValueError("Summary counters do not match raw evidence")
    actions = read_json(root / "actions.json")
    if any(a["timed_out"] for a in actions):
        raise ValueError("Timed-out action in a completed run")
    for action in actions:
        if not action["issued_ns"] <= action["input_ack_ns"] <= action["first_feedback_ns"]:
            raise ValueError("Invalid action timing order")
    return observations, actions


def bootstrap_pairs(pairs):
    if not pairs:
        return None
    # Each resampling unit contains both independently run strategies.
    data = np.array([[p["O0"]["model_visible_observations"], p["O1"]["model_visible_observations"],
                      sum(r["candidate_observations"] for r in p.values()),
                      sum(r["exact_repeat_opportunities"] for r in p.values()),
                      p["O1"]["task_wall_ms"] - p["O0"]["task_wall_ms"]] for p in pairs])
    indices = np.random.default_rng(65537).integers(0, len(pairs), size=(10000, len(pairs)))
    sampled = data[indices]
    totals = sampled.sum(axis=1)

    def measure(estimate, replicates):
        return {"estimate": float(estimate),
                "ci95": [float(x) for x in np.quantile(replicates, [.025, .975])]}

    sums = data.sum(axis=0)
    return {"n_pairs": len(pairs),
            "live_image_reduction": measure(1 - sums[1] / sums[0], 1 - totals[:, 1] / totals[:, 0]),
            "same_trace_image_reduction": measure(sums[3] / sums[2], totals[:, 3] / totals[:, 2]),
            "paired_task_wall_delta_ms": measure(np.median(data[:, 4]), np.median(sampled[:, :, 4], axis=1))}


def summarize(runs, observations, actions):
    report = {"n": len(runs), "success": sum(bool(r["success"]) for r in runs)}
    for key in ("candidate_observations", "model_visible_observations", "suppressed_observations",
                "captured_pixels", "model_visible_pixels", "false_suppressions", "missed_changes",
                "reconstruction_errors", "exact_repeat_opportunities", "model_calls"):
        report[key] = sum(r[key] for r in runs)
    for key in ("task_wall_ms", "controller_wall_ms", "launch_ms", "oracle_after_controller_ms"):
        report[key] = quantiles([r[key] for r in runs])
    for key in ("capture_ns", "serialize_ns", "context_ns", "compare_ns", "gate_ns", "receive_ns", "sample_ns"):
        report[key.replace("_ns", "_ms")] = quantiles([r[key] / 1e6 for r in observations])
    for key in ("input_ack_ms", "first_feedback_ms", "first_changed_feedback_ms", "public_effect_ms"):
        report[key] = quantiles([r.get(key) for r in actions])
    report["actions_without_changed_feedback"] = sum(r.get("first_changed_feedback_ms") is None for r in actions)
    report["by_observation_reason"] = {}
    for reason in sorted(set(r["reason"] for r in observations)):
        subset = [r for r in observations if r["reason"] == reason]
        report["by_observation_reason"][reason] = {"candidates": len(subset),
                                                  "suppressed": sum(r["suppressed"] for r in subset),
                                                  "exact_repeats": sum(r["exact_unchanged"] for r in subset)}
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directories", type=Path, nargs="+")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    runs = []
    all_observations, all_actions = {}, {}
    grouped_pairs = defaultdict(dict)
    environments = []
    for directory in args.directories:
        complete = read_json(directory / "COMPLETE.json")
        local_runs = jsonl(directory / "runs.jsonl")
        schedule = read_json(directory / "schedule.json")
        env = read_json(directory / "environment.json")
        environments.append(env)
        if complete["runs"] != len(local_runs) or not all(r.get("success") and r.get("audit_pass") for r in local_runs):
            raise ValueError("Incomplete or failed suite: no PASS analysis")
        expected = {(app, seed, strategy) for app, seed in schedule["pairs"] for strategy in schedule["strategies"]}
        actual = {(r["app"], r["seed"], r["strategy"]) for r in local_runs}
        if actual != expected or len(actual) != len(local_runs):
            raise ValueError("Missing or duplicate scheduled run")
        for r in local_runs:
            key = (r["app"], r["seed"])
            if r["strategy"] in grouped_pairs[key]:
                raise ValueError("Seed reuse across replicates")
            grouped_pairs[key][r["strategy"]] = r
            obs, acts = audit_run(directory / r["relative_path"], r)
            run_key = (*key, r["strategy"])
            all_observations[run_key], all_actions[run_key] = obs, acts
            runs.append(r)
    if any(env["code_sha256"] != environments[0]["code_sha256"]
           or env["parameters"] != environments[0]["parameters"]
           or env["versions"] != environments[0]["versions"] for env in environments):
        raise ValueError("Code, parameters or app versions differ between replicates")
    for pair in grouped_pairs.values():
        if set(pair) != {"O0", "O1"}:
            raise ValueError("Unpaired strategies")
        a, b = pair["O0"], pair["O1"]
        for field in ("a", "b", "dx", "token"):
            if a["goal"][field] != b["goal"][field]:
                raise ValueError("Paired task goals differ")
        if a["logical_ops"] != b["logical_ops"] or a["input_events"] != b["input_events"]:
            raise ValueError("Paired input schedule differs")
        ka, kb = (a["app"], a["seed"], "O0"), (b["app"], b["seed"], "O1")
        if [x["action_id"] for x in all_actions[ka]] != [x["action_id"] for x in all_actions[kb]]:
            raise ValueError("Paired action order differs")
    report = {"directories": [str(p) for p in args.directories], "archive_audit": "PASS", "apps": {}}
    for app in sorted({r["app"] for r in runs}) + ["all"]:
        subset = [r for r in runs if app == "all" or r["app"] == app]
        stats = {"paired": bootstrap_pairs([pair for (name, seed), pair in grouped_pairs.items()
                                              if app == "all" or name == app])}
        for strategy in ("O0", "O1"):
            selected = [r for r in subset if r["strategy"] == strategy]
            keys = [(r["app"], r["seed"], strategy) for r in selected]
            stats[strategy] = summarize(selected, [o for k in keys for o in all_observations[k]],
                                       [a for k in keys for a in all_actions[k]])
        report["apps"][app] = stats
    same_trace = report["apps"]["all"]["paired"]["same_trace_image_reduction"]
    report["efficiency_gate"] = "PASS" if same_trace["estimate"] >= .1 and same_trace["ci95"][0] > 0 else "HOLD"
    report["scope"] = "Local scripted real-GUI experiment; fresh protocol completion is assessed separately; no model/tokens"
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "summary.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    with (args.out / "summary.csv").open("w", newline="") as stream:
        fields = ["app", "strategy", "n", "success", "candidate_observations", "model_visible_observations",
                  "suppressed_observations", "captured_pixels", "model_visible_pixels", "false_suppressions",
                  "task_wall_p50_ms", "task_wall_p95_ms", "task_wall_p99_ms", "first_feedback_p50_ms",
                  "first_feedback_p95_ms", "first_feedback_p99_ms", "compare_p50_ms", "compare_p95_ms", "compare_p99_ms"]
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for app, stats in report["apps"].items():
            for strategy in ("O0", "O1"):
                row = {"app": app, "strategy": strategy}
                for field in fields[2:]:
                    row[field] = stats[strategy].get(field)
                for dest, src in (("task_wall", "task_wall_ms"), ("first_feedback", "first_feedback_ms"),
                                  ("compare", "compare_ms")):
                    for p in (50, 95, 99):
                        row[f"{dest}_p{p}_ms"] = stats[strategy][src][f"p{p}"]
                writer.writerow(row)
    print(json.dumps({"archive_audit": report["archive_audit"], "efficiency_gate": report["efficiency_gate"],
                      "paired": report["apps"]["all"]["paired"]}, indent=2))


if __name__ == "__main__":
    main()
