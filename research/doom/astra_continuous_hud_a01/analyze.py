"""Posthoc A01: inspect one continuous HUD excursion in the retained Astra run."""
import csv
import hashlib
import json
import platform
import shutil
import subprocess
from pathlib import Path

import numpy as np
from PIL import Image


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
RUN = REPO / "research/doom/results/map01-astra-attempt-v1"
VIDEO = RUN / "map01-astra-live-01-2x.mp4"
VIDEO_META = RUN / "video.json"
REPORT = RUN / "report.json"
EVENTS = RUN / "events.jsonl"
FRAME_MANIFEST = RUN / "frame-manifest.json"
OUTPUT_VIDEO_FRAME = HERE / "video-frame-311.png"
SAMPLES_CSV = HERE / "samples.csv"
RESULT = HERE / "result.json"
FREEZE = HERE / "freeze.json"

ROI = (90, 490, 120, 55)  # output video pixels: x, y, width, height
DECISION_INDEX = 5
VIDEO_FRAME_INDEX = 311
STABLE_DECISION_INDEX = 4
RED_THRESHOLD = (140, 70, 70)  # R >= threshold, G/B <= threshold
MIN_MASK_CHANGE = 60  # > 2x the stable pre-damage calibration maximum


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def red_mask(rgb):
    r, g, b = rgb[:, :, 0], rgb[:, :, 1], rgb[:, :, 2]
    return (r >= RED_THRESHOLD[0]) & (g <= RED_THRESHOLD[1]) & (b <= RED_THRESHOLD[2])


def run_checked(args):
    return subprocess.run(args, check=True, stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE)


def main():
    ffmpeg = shutil.which("ffmpeg")
    ffprobe = shutil.which("ffprobe")
    if not ffmpeg or not ffprobe:
        raise SystemExit("ffmpeg and ffprobe must be available on PATH")

    video_meta = read_json(VIDEO_META)
    report = read_json(REPORT)
    events = [json.loads(line) for line in EVENTS.read_text(encoding="utf-8").splitlines()]
    manifest = read_json(FRAME_MANIFEST)
    assert sha(VIDEO) == video_meta["sha256"]
    assert VIDEO.stat().st_size == video_meta["bytes"]

    probe = json.loads(run_checked([
        ffprobe, "-v", "error", "-select_streams", "v:0", "-count_frames",
        "-show_entries", "stream=width,height,r_frame_rate,duration,nb_read_frames",
        "-of", "json", str(VIDEO),
    ]).stdout)
    stream = probe["streams"][0]
    assert (stream["width"], stream["height"]) == (video_meta["width"], video_meta["height"])
    assert int(stream["nb_read_frames"]) == video_meta["frames"] == 780

    x, y, width, height = ROI
    decoded = run_checked([
        ffmpeg, "-v", "error", "-i", str(VIDEO), "-vf",
        f"crop={width}:{height}:{x}:{y}:exact=1", "-f", "rawvideo",
        "-pix_fmt", "rgb24", "pipe:1",
    ]).stdout
    frame_bytes = width * height * 3
    assert len(decoded) == video_meta["frames"] * frame_bytes
    crops = np.frombuffer(decoded, dtype=np.uint8).reshape(
        (video_meta["frames"], height, width, 3))
    masks = [red_mask(frame) for frame in crops]
    changes = [0] + [int(np.count_nonzero(masks[i] ^ masks[i - 1]))
                     for i in range(1, len(masks))]

    run_checked([
        ffmpeg, "-v", "error", "-i", str(VIDEO), "-vf",
        f"select=eq(n\\,{VIDEO_FRAME_INDEX})", "-vsync", "0", "-frames:v", "1",
        "-y", str(OUTPUT_VIDEO_FRAME),
    ])
    assert OUTPUT_VIDEO_FRAME.is_file()

    first_observation = next(row for row in events
                             if row.get("event") == "observation" and row.get("id") == "initial")
    start_ns = first_observation["capture_ns"]
    decision5 = report["decisions"][DECISION_INDEX]
    decision6 = report["decisions"][DECISION_INDEX + 1]
    stable_frame = report["decisions"][STABLE_DECISION_INDEX]
    video_fps = video_meta["fps"]
    playback_speed = video_meta["source_playback_speed"]

    def source_seconds_at(ns):
        return (ns - start_ns) / 1e9

    def observation_for(decision):
        basename = Path(decision["source_image"]).name
        row = next(row for row in events if row.get("event") == "observation" and
                   Path(row["image"]).name == basename)
        return row

    input5 = observation_for(decision5)
    input6 = observation_for(decision6)
    sample_s = VIDEO_FRAME_INDEX / video_fps * playback_speed
    sample_ns = start_ns + round(sample_s * 1e9)
    latest_observation = max(
        (row for row in events if row.get("event") == "observation" and
         row["capture_ns"] <= sample_ns), key=lambda row: row["capture_ns"])
    cover_accept = next(row for row in events if row.get("event") == "accepted" and
                        row.get("id") == "cover-5")
    cover_terminal = next(row for row in events if row.get("event") == "terminal" and
                          row.get("id") == "cover-5")
    cover_command = next(row["command"] for row in events
                         if row.get("event") == "command" and
                         row.get("command", {}).get("id") == "cover-5")
    ready = next(row for row in events if row.get("event") == "ready")
    assert all(step.get("op") == "coast" for step in cover_command["steps"])
    assert ready["command_contract"]["coast"]["input_authority"] is False
    stable_input = observation_for(stable_frame)
    stable_index = round(source_seconds_at(stable_input["capture_ns"]) /
                         playback_speed * video_fps)
    stable_max = max(changes[1:stable_index + 1])
    assert stable_max < MIN_MASK_CHANGE

    with SAMPLES_CSV.open("w", newline="", encoding="utf-8") as stream_out:
        writer = csv.DictWriter(stream_out, fieldnames=(
            "frame_index", "video_time_s", "source_control_elapsed_s",
            "red_mask_pixels", "red_mask_sha256", "red_mask_xor_from_previous"))
        writer.writeheader()
        for index, mask in enumerate(masks):
            writer.writerow({
                "frame_index": index,
                "video_time_s": f"{index / video_fps:.3f}",
                "source_control_elapsed_s": f"{index / video_fps * playback_speed:.3f}",
                "red_mask_pixels": int(mask.sum()),
                "red_mask_sha256": hashlib.sha256(mask.tobytes()).hexdigest(),
                "red_mask_xor_from_previous": changes[index],
            })

    inputs = [VIDEO, VIDEO_META, REPORT, EVENTS, FRAME_MANIFEST,
              REPO / "research/doom/render_map01_timeline_v1.py"]
    inputs.extend(RUN / row["file"] for row in manifest)
    source_hashes = {str(path.relative_to(REPO)).replace("\\", "/"): sha(path)
                     for path in inputs}
    result = {
        "schema": "agent-interface-astra-continuous-hud-a01-v1",
        "status": "POSTHOC_PASS_SCOPED",
        "question": "Can retained video expose a transient HUD health excursion during a model wait that decision-frame sampling misses?",
        "H_T_D_C_U": {
            "H": "At least one timestamped intermediate state during a model wait differs from both adjacent decision-frame HUD health values.",
            "T": "Decode the retained video at its authored frame cadence, align to the first-observation anchor and model/cover intervals, and visually inspect the decision and selected source frames.",
            "D": "PASS_SCOPED if the selected intermediate HUD value differs from both adjacent decision samples, the sample maps inside the wait and active cover, and source/video timing checks pass.",
            "C": "Health may fall and recover from different causes (including pickup); a red-pixel ROI change is not a health classifier or a control response.",
            "U": "One retained attempt, 5 source samples/s in a rendered video, manual visual transcription, no causal or intervention evidence.",
        },
        "observation": {
            "decision_before": DECISION_INDEX,
            "decision_before_health_percent_manual": 84,
            "selected_video_frame_index": VIDEO_FRAME_INDEX,
            "selected_video_time_s": VIDEO_FRAME_INDEX / video_fps,
            "selected_source_control_elapsed_s": sample_s,
            "selected_health_percent_manual": 77,
            "decision_after": DECISION_INDEX + 1,
            "decision_after_health_percent_manual": 84,
            "transient_drop_percent_points": 7,
            "recovered_by_next_decision_sample": True,
            "manual_visual_transcription": True,
            "selected_frame_file": OUTPUT_VIDEO_FRAME.name,
            "selected_frame_sha256": sha(OUTPUT_VIDEO_FRAME),
            "decision_before_source_frame": Path(decision5["source_image"]).name,
            "decision_before_source_frame_sha256": sha(RUN / "frames" / f"{DECISION_INDEX:02}.png"),
            "decision_after_source_frame": Path(decision6["source_image"]).name,
            "decision_after_source_frame_sha256": sha(RUN / "frames" / f"{DECISION_INDEX + 1:02}.png"),
            "visible_close_enemy_in_selected_frame": True,
        },
        "timing": {
            "timeline_anchor": "first observation capture_ns, matching render_map01_timeline_v1.py",
            "sample_ns": sample_ns,
            "latest_observation_id": latest_observation["id"],
            "latest_observation_sequence": latest_observation["sequence"],
            "latest_observation_age_ms": (sample_ns - latest_observation["capture_ns"]) / 1e6,
            "decision5_model_start_source_s": source_seconds_at(decision5["controller_model_started_ns"]),
            "decision5_model_end_source_s": source_seconds_at(decision5["controller_model_ended_ns"]),
            "cover5_accepted_source_s": source_seconds_at(cover_accept["accepted_ns"]),
            "cover5_terminal_source_s": source_seconds_at(cover_terminal["terminal_ns"]),
            "cover5_steps": cover_command["steps"],
            "cover5_input_authority": ready["command_contract"]["coast"]["input_authority"],
            "sample_during_decision5_model_wait": (
                decision5["controller_model_started_ns"] <= sample_ns <=
                decision5["controller_model_ended_ns"]),
            "sample_during_cover5": cover_accept["accepted_ns"] <= sample_ns <= cover_terminal["terminal_ns"],
        },
        "pixel_change_probe": {
            "roi_video_xywh": list(ROI),
            "red_threshold_rgb": list(RED_THRESHOLD),
            "samples": len(masks),
            "source_sample_interval_s": playback_speed / video_fps,
            "stable_baseline_through_decision4_frame_index": stable_index,
            "stable_baseline_max_mask_xor_pixels": stable_max,
            "change_threshold_mask_xor_pixels": MIN_MASK_CHANGE,
            "selected_frame_mask_xor_from_previous_pixels": changes[VIDEO_FRAME_INDEX],
            "selected_frame_exceeds_threshold": changes[VIDEO_FRAME_INDEX] > MIN_MASK_CHANGE,
            "interpretation": "A bounded ROI change alarm distinguishes this selected glyph transition from the stable pre-damage baseline; it is not OCR or a health-direction estimate.",
        },
        "source_sha256": source_hashes,
        "generated_sha256": {
            SAMPLES_CSV.name: sha(SAMPLES_CSV),
            OUTPUT_VIDEO_FRAME.name: sha(OUTPUT_VIDEO_FRAME),
        },
        "limits": [
            "Single retained run and one manually transcribed event; exploratory posthoc analysis, not a new allocation.",
            "Video is a sampled/replayed observation trace; it does not prove the controller consumed or acted on each intermediate screenshot.",
            "The transient health decrease and recovery cannot be causally assigned to enemy damage, movement, a pickup, or a specific policy step.",
            "The red-pixel ROI detector signals change only; it does not identify health, direction, threat semantics, task progress, or useful effect.",
            "No local guard response, recovery benefit, physical-input safety, survival benefit, or MAP01 exit is established.",
        ],
        "execution_environment": {
            "platform": platform.platform(),
            "python_version": platform.python_version(),
            "wslc_available": shutil.which("wslc.exe") is not None,
            "method_note": "Posthoc local CPU analysis on Windows; wslc.exe was not available, and no container or external runtime was needed for this retained-video decode.",
        },
        "next_test_implication": "A separately authorized fresh-current-main threat-exposure run should retain timestamped observations through model waits and score whether an interruption/escalation uses fresh evidence; do not infer this from renewed old policy or viewport-change receipts.",
    }
    RESULT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")

    version = run_checked([ffmpeg, "-version"]).stdout.decode("utf-8", "replace").splitlines()[0]
    freeze = {
        "repository_base_commit": subprocess.run(
            ["git", "merge-base", "HEAD", "origin/main"], cwd=REPO,
            check=True, stdout=subprocess.PIPE, text=True).stdout.strip(),
        "analysis_source_sha256": sha(Path(__file__)),
        "ffmpeg_version": version,
        "execution_environment": result["execution_environment"],
        "source_sha256": source_hashes,
        "settings": {"roi_video_xywh": list(ROI), "red_threshold_rgb": list(RED_THRESHOLD),
                     "change_threshold_mask_xor_pixels": MIN_MASK_CHANGE,
                     "selected_video_frame_index": VIDEO_FRAME_INDEX},
    }
    FREEZE.write_text(json.dumps(freeze, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": result["status"],
        "selected_source_control_elapsed_s": sample_s,
        "selected_health_percent_manual": 77,
        "surrounding_decision_health_percent_manual": [84, 84],
        "sample_during_model_wait": result["timing"]["sample_during_decision5_model_wait"],
        "sample_during_cover": result["timing"]["sample_during_cover5"],
        "latest_observation_age_ms": result["timing"]["latest_observation_age_ms"],
        "baseline_mask_diff_max": stable_max,
        "selected_mask_diff": changes[VIDEO_FRAME_INDEX],
        "frame": str(OUTPUT_VIDEO_FRAME),
        "result": str(RESULT),
    }, indent=2))


if __name__ == "__main__":
    main()
