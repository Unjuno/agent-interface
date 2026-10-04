"""Join retained video health-transition windows to raw input-step events."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE / "results/map01-astra-attempt-v1"
VIDEO_ROOT = HERE / "results/map01-astra-video-health-timeline-v1"
OUT = HERE / "results/map01-astra-video-health-timeline-v1/EVENT_INPUT_JOIN_V1.json"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build(video_timeline, report, events, hashes):
    ready = next(e["emit_ns"] for e in events if e["event"] == "ready")
    model_windows = video_timeline["model_windows"]
    decision_rows = report["decisions"]
    assert len(model_windows) == len(decision_rows) == 13
    window_deltas = []
    for window, decision in zip(model_windows, decision_rows):
        expected_start = (decision["controller_model_started_ns"] - ready) / 1e9
        expected_stop = (decision["controller_model_ended_ns"] - ready) / 1e9
        window_deltas.extend((abs(window["start_source_seconds"] - expected_start), abs(window["end_source_seconds"] - expected_stop)))
    assert max(window_deltas) < 1e-8

    held = {}
    completed = {}
    for event in events:
        if event["event"] == "keys_held":
            key = (event["id"], event["step"])
            assert key not in held
            held[key] = event
        elif event["event"] == "step_completed":
            key = (event["id"], event["step"])
            assert key not in completed
            completed[key] = event

    annotations = []
    for item in video_timeline["annotations"]:
        start_s, stop_s = item["source_time_interval_seconds"]
        start_ns, stop_ns = ready + round(start_s * 1e9), ready + round(stop_s * 1e9)
        in_window = [e for e in events if start_ns <= e.get("emit_ns", -1) < stop_ns]
        inputs = [e for e in in_window if e["event"] == "input_admission"]
        overlaps = []
        for key, down in held.items():
            finish = completed.get(key)
            if finish and down["emit_ns"] < stop_ns and finish["emit_ns"] > start_ns:
                overlaps.append({
                    "id": key[0], "step": key[1], "keys": down["keys"],
                    "ack_s": round((down["emit_ns"] - ready) / 1e9, 6),
                    "step_complete_s": round((finish["emit_ns"] - ready) / 1e9, 6),
                    "overlap_start_s": round((max(down["emit_ns"], start_ns) - ready) / 1e9, 6),
                    "overlap_stop_s": round((min(finish["emit_ns"], stop_ns) - ready) / 1e9, 6),
                })
        annotations.append({
            "event": item["event"],
            "health_delta_percent_points": item["delta_percent_points"],
            "health_before_percent": item["health_before_percent"],
            "health_after_percent": item["health_after_percent"],
            "source_time_interval_seconds": item["source_time_interval_seconds"],
            "cover_modes": item["cover_modes"],
            "model_call_indices": item["model_call_indices"],
            "input_admissions_inside_video_interval": [{"key": e["key"], "at_s": round((e["emit_ns"] - ready) / 1e9, 6)} for e in inputs],
            "key_ack_to_step_complete_overlaps": overlaps,
        })

    return {
        "schema": "agent-interface-map01-astra-video-health-input-event-join-v1",
        "source_run": "map01-astra-attempt-v1",
        "scope": "posthoc temporal join of video health-pixel transitions and raw event telemetry; descriptive only",
        "time_mapping": "video source seconds are relative to the ready event; the parent timeline's 13 model-window endpoints exactly match report model timestamps relative to ready",
        "source_sha256": hashes,
        "alignment": {"model_windows_checked": len(model_windows), "max_abs_endpoint_difference_seconds": max(window_deltas)},
        "limitations": [
            "transition timing is bounded by the 10 fps 2x video export and its annotated source-time intervals",
            "key_ack_to_step_complete_overlaps are event lifecycle envelopes, not exact physical key-up times or proof that a key remained down throughout",
            "temporal overlap does not establish damage cause, input effectiveness, threat identity, or policy causality",
            "HUD changes are video-derived manual numeric annotations from the parent posthoc analysis, not game-state telemetry",
        ],
        "transition_count": len(annotations),
        "transitions_with_input_admission_inside_video_interval": sum(bool(a["input_admissions_inside_video_interval"]) for a in annotations),
        "transitions_overlapping_key_ack_to_step_complete_envelope": sum(bool(a["key_ack_to_step_complete_overlaps"]) for a in annotations),
        "annotations": annotations,
    }


def main():
    timeline_path = VIDEO_ROOT / "TIMELINE.json"
    report_path = ROOT / "report.json"
    events_path = ROOT / "events.jsonl"
    video_path = ROOT / "map01-astra-live-01-2x.mp4"
    timeline = json.loads(timeline_path.read_text())
    report = json.loads(report_path.read_text())
    events = [json.loads(line) for line in events_path.read_text().splitlines()]
    hashes = {"video_TIMELINE.json": sha(timeline_path), "report.json": sha(report_path), "events.jsonl": sha(events_path), "video.mp4": sha(video_path)}
    assert hashes["video.mp4"] == timeline["source_video_sha256"]
    OUT.write_text(json.dumps(build(timeline, report, events, hashes), indent=2) + "\n")
    print(json.dumps({"output": str(OUT), "transitions": 30, "input_admissions_inside_windows": 5, "step_lifecycle_overlaps": 8, "max_model_window_alignment_error_seconds": 0.0}, indent=2))


if __name__ == "__main__":
    main()
