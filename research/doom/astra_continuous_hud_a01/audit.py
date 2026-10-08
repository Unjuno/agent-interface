"""Independent audit of the retained-video HUD excursion analysis."""
import csv
import hashlib
import json
import shutil
import subprocess
from pathlib import Path

import numpy as np
from PIL import Image


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
RUN = REPO / "research/doom/results/map01-astra-attempt-v1"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def main():
    freeze = load(HERE / "freeze.json")
    result = load(HERE / "result.json")
    report = load(RUN / "report.json")
    events = [json.loads(line) for line in
              (RUN / "events.jsonl").read_text(encoding="utf-8").splitlines()]
    meta = load(RUN / "video.json")
    for relative, expected in freeze["source_sha256"].items():
        assert sha(REPO / relative) == expected, relative
    assert sha(HERE / "analyze.py") == freeze["analysis_source_sha256"]
    assert result["source_sha256"] == freeze["source_sha256"]
    subprocess.run(["git", "merge-base", "--is-ancestor",
                    freeze["repository_base_commit"], "HEAD"], cwd=REPO,
                   check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    ffmpeg = shutil.which("ffmpeg")
    assert ffmpeg
    index = freeze["settings"]["selected_video_frame_index"]
    raw = subprocess.run([
        ffmpeg, "-v", "error", "-i", str(RUN / meta["file"]), "-vf",
        f"select=eq(n\\,{index})", "-vsync", "0", "-frames:v", "1",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "pipe:1",
    ], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout
    stored = np.asarray(Image.open(HERE / "video-frame-311.png").convert("RGB"))
    assert raw == stored.tobytes()
    assert sha(HERE / "video-frame-311.png") == result["observation"]["selected_frame_sha256"]

    with (HERE / "samples.csv").open(newline="", encoding="utf-8") as stream:
        samples = list(csv.DictReader(stream))
    assert len(samples) == meta["frames"] == 780
    fps = meta["fps"]
    speed = meta["source_playback_speed"]
    for i, row in enumerate(samples):
        assert int(row["frame_index"]) == i
        assert abs(float(row["video_time_s"]) - i / fps) < 0.0005
        assert abs(float(row["source_control_elapsed_s"]) - i / fps * speed) < 0.0005

    roi = freeze["settings"]["roi_video_xywh"]
    x, y, width, height = roi
    decoded = subprocess.run([
        ffmpeg, "-v", "error", "-i", str(RUN / meta["file"]), "-vf",
        f"crop={width}:{height}:{x}:{y}:exact=1", "-f", "rawvideo",
        "-pix_fmt", "rgb24", "pipe:1",
    ], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout
    frame_bytes = width * height * 3
    assert len(decoded) == len(samples) * frame_bytes
    crops = np.frombuffer(decoded, dtype=np.uint8).reshape((-1, height, width, 3))
    red = freeze["settings"]["red_threshold_rgb"]
    masks = [(f[:, :, 0] >= red[0]) & (f[:, :, 1] <= red[1]) &
             (f[:, :, 2] <= red[2]) for f in crops]
    changes = [0] + [int(np.count_nonzero(masks[i] ^ masks[i - 1]))
                     for i in range(1, len(masks))]
    assert changes == [int(row["red_mask_xor_from_previous"]) for row in samples]

    selected = result["observation"]["selected_video_frame_index"]
    assert result["observation"]["decision_before_health_percent_manual"] == 84
    assert result["observation"]["selected_health_percent_manual"] == 77
    assert result["observation"]["decision_after_health_percent_manual"] == 84
    assert result["observation"]["visible_close_enemy_in_selected_frame"] is True
    selected_s = selected / fps * speed
    assert abs(selected_s - 62.2) < 1e-9
    decision5 = report["decisions"][5]
    decision6 = report["decisions"][6]
    initial = next(row for row in events if row.get("event") == "observation" and
                   row.get("id") == "initial")
    sample_ns = initial["capture_ns"] + round(selected_s * 1e9)
    assert decision5["controller_model_started_ns"] <= sample_ns <= decision5["controller_model_ended_ns"]
    assert sample_ns < decision6["controller_model_started_ns"]
    cover_accept = next(row for row in events if row.get("event") == "accepted" and
                        row.get("id") == "cover-5")
    cover_terminal = next(row for row in events if row.get("event") == "terminal" and
                          row.get("id") == "cover-5")
    assert cover_accept["accepted_ns"] <= sample_ns <= cover_terminal["terminal_ns"]
    cover_command = next(row["command"] for row in events
                         if row.get("event") == "command" and
                         row.get("command", {}).get("id") == "cover-5")
    ready = next(row for row in events if row.get("event") == "ready")
    assert all(step.get("op") == "coast" for step in cover_command["steps"])
    assert ready["command_contract"]["coast"]["input_authority"] is False
    latest = max((row for row in events if row.get("event") == "observation" and
                  row["capture_ns"] <= sample_ns), key=lambda row: row["capture_ns"])
    assert latest["id"] == result["timing"]["latest_observation_id"] == "cover-5"
    assert latest["sequence"] == result["timing"]["latest_observation_sequence"] == 226
    age_ms = (sample_ns - latest["capture_ns"]) / 1e6
    assert abs(age_ms - result["timing"]["latest_observation_age_ms"]) < 1e-6
    assert age_ms < speed / fps * 1000

    stable_index = result["pixel_change_probe"]["stable_baseline_through_decision4_frame_index"]
    stable_max = max(changes[1:stable_index + 1])
    selected_change = changes[selected]
    threshold = result["pixel_change_probe"]["change_threshold_mask_xor_pixels"]
    assert stable_max == result["pixel_change_probe"]["stable_baseline_max_mask_xor_pixels"] == 29
    assert selected_change == result["pixel_change_probe"]["selected_frame_mask_xor_from_previous_pixels"] == 471
    assert threshold == 60 and threshold > 2 * stable_max
    assert selected_change > threshold

    audit = {
        "schema": "agent-interface-astra-continuous-hud-a01-audit-v1",
        "status": "PASS_SCOPED",
        "checks": {
            "source_hashes": len(freeze["source_sha256"]),
            "decoded_video_frames": len(samples),
            "selected_frame_pixels_equal_video_decode": True,
            "timeline_mapping_matches_renderer": True,
            "selected_observation_inside_model_wait_and_cover": True,
            "active_cover_was_no_input_coast": True,
            "latest_observation_age_ms": age_ms,
            "stable_baseline_mask_diff_max": stable_max,
            "selected_mask_diff": selected_change,
            "selected_visual_change_exceeds_threshold": True,
        },
        "manual_visual_review": {
            "status": "PASS_VISUAL_INSPECTION",
            "decision5_health_percent": 84,
            "frame311_health_percent": 77,
            "decision6_health_percent": 84,
            "close_enemy_visible_at_frame311": True,
            "checked_images": [
                "../results/map01-astra-attempt-v1/frames/05.png",
                "video-frame-311.png",
                "../results/map01-astra-attempt-v1/frames/06.png",
            ],
            "limitation": "These labels were visually inspected during this analysis; they are not OCR output or an independent game-state channel.",
        },
        "scope": "One posthoc visual sample in one retained run; no causal, controller-response, safety, survival, or task-completion claim.",
        "result_sha256": sha(HERE / "result.json"),
        "samples_csv_sha256": sha(HERE / "samples.csv"),
        "selected_frame_sha256": sha(HERE / "video-frame-311.png"),
    }
    (HERE / "audit.json").write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(audit, indent=2))


if __name__ == "__main__":
    main()
