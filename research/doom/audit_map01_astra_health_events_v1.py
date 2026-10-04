"""Independent raw-source audit for the video-transition/input-event join."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE / "results/map01-astra-attempt-v1"
VIDEO_ROOT = HERE / "results/map01-astra-video-health-timeline-v1"
OUTPUT = VIDEO_ROOT / "EVENT_INPUT_JOIN_V1.json"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit(result, timeline, report, events, hashes):
    assert result["schema"] == "agent-interface-map01-astra-video-health-input-event-join-v1"
    assert result["source_sha256"] == hashes
    assert result["alignment"]["model_windows_checked"] == 13
    assert result["alignment"]["max_abs_endpoint_difference_seconds"] < 1e-8
    ready = next(e["emit_ns"] for e in events if e.get("event") == "ready")
    for window, decision in zip(timeline["model_windows"], report["decisions"]):
        a = (decision["controller_model_started_ns"] - ready) / 1e9
        b = (decision["controller_model_ended_ns"] - ready) / 1e9
        assert abs(window["start_source_seconds"] - a) < 1e-8
        assert abs(window["end_source_seconds"] - b) < 1e-8

    down_by_identity = {(e.get("id"), e.get("step")): e for e in events if e.get("event") == "keys_held"}
    done_by_identity = {(e.get("id"), e.get("step")): e for e in events if e.get("event") == "step_completed"}
    assert len(down_by_identity) == sum(e["event"] == "keys_held" for e in events)
    assert len(done_by_identity) == sum(e["event"] == "step_completed" for e in events)
    annotations = result["annotations"]
    assert len(annotations) == len(timeline["annotations"]) == 30
    for actual, source in zip(annotations, timeline["annotations"]):
        start, stop = source["source_time_interval_seconds"]
        t0, t1 = ready + round(start * 1e9), ready + round(stop * 1e9)
        interval_inputs = [e for e in events if e.get("event") == "input_admission" and t0 <= e.get("emit_ns", -1) < t1]
        expected_inputs = [{"key": e["key"], "at_s": round((e["emit_ns"] - ready) / 1e9, 6)} for e in interval_inputs]
        envelopes = []
        for identity, down in down_by_identity.items():
            up = done_by_identity.get(identity)
            if up and down["emit_ns"] < t1 and up["emit_ns"] > t0:
                envelopes.append({
                    "id": identity[0], "step": identity[1], "keys": down["keys"],
                    "ack_s": round((down["emit_ns"] - ready) / 1e9, 6),
                    "step_complete_s": round((up["emit_ns"] - ready) / 1e9, 6),
                    "overlap_start_s": round((max(down["emit_ns"], t0) - ready) / 1e9, 6),
                    "overlap_stop_s": round((min(up["emit_ns"], t1) - ready) / 1e9, 6),
                })
        assert actual["event"] == source["event"]
        assert actual["health_delta_percent_points"] == source["delta_percent_points"]
        assert actual["health_before_percent"] == source["health_before_percent"]
        assert actual["health_after_percent"] == source["health_after_percent"]
        assert actual["source_time_interval_seconds"] == source["source_time_interval_seconds"]
        assert actual["cover_modes"] == source["cover_modes"]
        assert actual["model_call_indices"] == source["model_call_indices"]
        assert actual["input_admissions_inside_video_interval"] == expected_inputs
        assert actual["key_ack_to_step_complete_overlaps"] == envelopes
    assert result["transitions_with_input_admission_inside_video_interval"] == 5
    assert result["transitions_overlapping_key_ack_to_step_complete_envelope"] == 8


def load_inputs():
    timeline_path, report_path = VIDEO_ROOT / "TIMELINE.json", ROOT / "report.json"
    events_path, video_path = ROOT / "events.jsonl", ROOT / "map01-astra-live-01-2x.mp4"
    hashes = {"video_TIMELINE.json": sha(timeline_path), "report.json": sha(report_path), "events.jsonl": sha(events_path), "video.mp4": sha(video_path)}
    timeline = json.loads(timeline_path.read_text())
    assert hashes["video.mp4"] == timeline["source_video_sha256"]
    return (json.loads(OUTPUT.read_text()), timeline, json.loads(report_path.read_text()),
            [json.loads(line) for line in events_path.read_text().splitlines()], hashes)


def main():
    audit(*load_inputs())
    print(json.dumps({"passed": True, "model_windows": 13, "health_transitions": 30, "input_admission_overlaps": 5, "key_ack_to_step_complete_overlaps": 8}, indent=2))


if __name__ == "__main__":
    main()
