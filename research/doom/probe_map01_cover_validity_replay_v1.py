"""Model-free typed health-envelope replay over the retained v28 exact trace."""
import argparse
import hashlib
import json
from pathlib import Path
import statistics
import sys
import time


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(HERE.parent / "live_control"))
from observable_signal_guard_v1 import ObservableSignalGuard, ObservableSignalPolicyMonitor
from doom_hud_signal_v1 import DoomStatusNumberReader


SOURCE = HERE / "results/map01-fixed-threat-v28-live-01"
CROSS_SOURCE = HERE / "results/map01-cover-threat-v23-live-02"
WAD = REPO / "_vizdoom/vizdoom/freedoom2.wad"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def percentile(values, probability):
    ordered = sorted(values)
    index = (len(ordered) - 1) * probability
    lower = int(index)
    upper = min(lower + 1, len(ordered) - 1)
    weight = index - lower
    return ordered[lower] * (1 - weight) + ordered[upper] * weight


def cross_trace_validation(reader):
    index = json.loads((CROSS_SOURCE / "decision-frame-index.json").read_text())
    audit = json.loads((CROSS_SOURCE / "audit.json").read_text())
    events = [json.loads(line) for line in
              (CROSS_SOURCE / "runtime/events.jsonl").read_text().splitlines()]
    observations = {row["sequence"]: row for row in events
                    if row.get("event") == "observation"}
    expected = audit["visual_transcription"]["health"]
    if len(index) != len(expected):
        raise RuntimeError("cross-trace index/manual review length mismatch")
    rows = []
    for item, expected_value in zip(index, expected):
        frame = CROSS_SOURCE / item["retained"]
        if sha(frame) != item["sha256"]:
            raise RuntimeError("cross-trace retained frame hash mismatch")
        sequence = int(Path(item["original"]).stem)
        observation = dict(observations[sequence])
        if observation.get("exact") is not True:
            raise RuntimeError("cross-trace observation is not exact")
        observation["image"] = str(frame)
        reading = reader.read(observation)
        rows.append({"iteration": item["iteration"], "sequence": sequence,
                     "expected_health": expected_value,
                     "observed_health": reading.get("value"),
                     "status": reading["status"], "exact": True,
                     "frame_sha256": item["sha256"]})
    if len(rows) != len(index) or any(
            row["status"] != "observed" or
            row["observed_health"] != row["expected_health"] for row in rows):
        raise RuntimeError("cross-trace manual health mismatch")
    return rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--hard-minimum", type=int, default=80)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=False)

    events = [json.loads(line) for line in (SOURCE / "runtime/events.jsonl").read_text().splitlines()]
    observations = [row for row in events if row.get("event") == "observation"]
    if not observations or not all(row.get("exact") is True for row in observations):
        raise RuntimeError("replay requires exact retained observations")
    reader = DoomStatusNumberReader(
        WAD, image_resolver=lambda value: SOURCE / "runtime" / Path(value).name)
    readings = []
    durations = []
    for observation in observations:
        started = time.perf_counter_ns()
        reading = reader.read(observation)
        durations.append((time.perf_counter_ns() - started) / 1e6)
        readings.append(reading)
    if not all(row["status"] == "observed" for row in readings):
        raise RuntimeError("retained exact frame signal extraction failed closed")

    transitions = []
    previous = None
    for reading in readings:
        if reading["value"] != previous:
            transitions.append({"sequence": reading["sequence"], "health": reading["value"],
                                "capture_ns": reading["capture_ns"]})
            previous = reading["value"]

    by_sequence = {row["sequence"]: row for row in readings}
    source = by_sequence[37]
    spec = {
        "op": "observable_signal_guard", "guard_id": "map01-health-development-1",
        "source_sequence": 37, "signal_id": "health", "source_value": source["value"],
        "hard_minimum": args.hard_minimum, "max_source_age_ms": 30000,
        "on_soft_change": "preserve_existing_policy",
        "on_hard_change": "needs_decision", "on_unknown": "needs_decision",
    }
    guard = ObservableSignalGuard(spec, source, source["binding"])
    monitor = ObservableSignalPolicyMonitor(guard, reader)
    hard_event = None
    for observation in observations:
        if observation["sequence"] <= source["sequence"]:
            continue
        hard_event = monitor.observe(observation)
        if hard_event is not None:
            break
    if hard_event is None:
        raise RuntimeError("development hard minimum was not exposed")

    baseline = json.loads((SOURCE / "report.json").read_text())["decisions"][2]["policy_invalidation"]
    manual = json.loads((SOURCE / "analysis/threat-review.json").read_text())
    manual_values = {int(Path(row["frame"]).stem): row["health"] for row in manual["rows"]}
    reviewed = {sequence: by_sequence[sequence]["value"] for sequence in manual_values}
    assert reviewed == manual_values
    cross_reader = DoomStatusNumberReader(WAD)
    cross_rows = cross_trace_validation(cross_reader)
    hard_capture_ns = hard_event["signal"]["capture_ns"]
    report = {
        "schema": "map01-cover-validity-replay-v1",
        "status": "DEVELOPMENT_REPLAY_PASS",
        "model_calls": 0,
        "source_allocation": "map01-fixed-threat-v28-live-01",
        "exact_observations_scanned": len(observations),
        "observed_signals": len(readings),
        "unknown_signals": 0,
        "manually_reviewed_values": manual_values,
        "reviewed_values_match": True,
        "independent_cross_trace": {
            "source_allocation": "map01-cover-threat-v23-live-02",
            "exact_retained_decision_frames": len(cross_rows),
            "manually_reviewed_values_matched": len(cross_rows),
            "unknown_signals": 0,
            "rows": cross_rows,
        },
        "health_transitions": transitions,
        "candidate": {
            "source_sequence": source["sequence"], "source_health": source["value"],
            "hard_minimum": args.hard_minimum,
            "soft_transition_count": monitor.soft_event_count,
            "latest_soft_event": monitor.latest_soft_event,
            "hard_event": hard_event,
            "grants_new_input_authority": False,
        },
        "baseline_first_change_sequence": baseline["sequence"],
        "candidate_hard_sequence": hard_event["sequence"],
        "additional_exact_samples_before_hard_stop": hard_event["sequence"] - baseline["sequence"],
        "baseline_change_to_candidate_hard_ms":
            (hard_capture_ns - baseline["capture_ns"]) / 1e6,
        "extraction_ms": {
            "median": statistics.median(durations),
            "p95": percentile(durations, .95),
            "max": max(durations),
        },
        "source_sha256": {
            "research/doom/doom_hud_signal_v1.py": sha(HERE / "doom_hud_signal_v1.py"),
            "research/live_control/observable_signal_guard_v1.py":
                sha(HERE.parent / "live_control/observable_signal_guard_v1.py"),
            "research/doom/results/map01-fixed-threat-v28-live-01/report.json":
                sha(SOURCE / "report.json"),
            "research/doom/results/map01-fixed-threat-v28-live-01/runtime/events.jsonl":
                sha(SOURCE / "runtime/events.jsonl"),
            "research/doom/results/map01-cover-threat-v23-live-02/audit.json":
                sha(CROSS_SOURCE / "audit.json"),
            "research/doom/results/map01-cover-threat-v23-live-02/decision-frame-index.json":
                sha(CROSS_SOURCE / "decision-frame-index.json"),
            "research/doom/results/map01-cover-threat-v23-live-02/runtime/events.jsonl":
                sha(CROSS_SOURCE / "runtime/events.jsonl"),
        },
        "interpretation": "typed direction separates pickup/soft loss/hard floor while preserving one-way authority",
        "limits": "posthoc floor selected after inspecting one retained trace; counterfactual planner completion, survival, latency, token or general accuracy is not established",
    }
    (args.out / "report.json").write_text(json.dumps(report, indent=2) + "\n",
                                           encoding="utf-8", newline="\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
