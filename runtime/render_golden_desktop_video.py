"""Render a labelled 2x playback from exact retained golden-demo observations."""

from __future__ import annotations

import argparse
import bisect
import hashlib
import json
import subprocess
import tempfile
from pathlib import Path

import cv2
import imageio_ffmpeg
import numpy as np


ROOT = Path(__file__).resolve().parents[1]


def read_lines(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def phase_at(details: list[dict], timestamp: int) -> tuple[str, str, str]:
    for index, detail in enumerate(details, 1):
        route = detail["trace"]["route"]
        for phase in detail["adaptive"]["phase_timings"]:
            if phase["started_ns"] <= timestamp <= phase["ended_ns"]:
                stage = phase["stage"]
                if stage in {"anchor_model", "expanded_model"}:
                    label = "MODEL GROUNDING"
                elif stage == "reuse_revalidate":
                    label = "LOCAL REVALIDATION"
                elif stage == "execute":
                    label = "CHECKED LOCAL EXECUTION"
                elif stage == "final_revalidate":
                    label = "FRESH TARGET CHECK"
                else:
                    label = "LOCAL OBSERVE / VERIFY"
                return f"TASK {index}/6", route.upper(), label
    return "SETUP / TRANSITION", "-", "LOCAL OBSERVATION"


def fit_frame(image: np.ndarray, width: int, height: int) -> np.ndarray:
    canvas = np.zeros((height, width, 3), dtype=np.uint8)
    scale = min(width / image.shape[1], height / image.shape[0])
    resized = cv2.resize(image, (round(image.shape[1] * scale), round(image.shape[0] * scale)))
    x = (width - resized.shape[1]) // 2
    y = (height - resized.shape[0]) // 2
    canvas[y:y + resized.shape[0], x:x + resized.shape[1]] = resized
    return canvas


def label_frame(image: np.ndarray, elapsed: float, duration: float,
                task: str, route: str, stage: str) -> np.ndarray:
    frame = np.zeros((image.shape[0] + 92, image.shape[1], 3), dtype=np.uint8)
    frame[92:] = image
    cv2.putText(frame, "AGENT INTERFACE  /  GOLDEN DESKTOP  /  EXACT EVIDENCE PLAYBACK  /  2x",
                (20, 26), cv2.FONT_HERSHEY_SIMPLEX, .55, (235, 235, 235), 1, cv2.LINE_AA)
    cv2.putText(frame, f"{task}   {route}   {stage}", (20, 56),
                cv2.FONT_HERSHEY_SIMPLEX, .63, (104, 220, 170), 2, cv2.LINE_AA)
    cv2.putText(frame, f"REAL TIMELINE {elapsed:05.1f}s / {duration:05.1f}s", (20, 81),
                cv2.FONT_HERSHEY_SIMPLEX, .46, (190, 190, 190), 1, cv2.LINE_AA)
    left, right = 430, frame.shape[1] - 20
    cv2.rectangle(frame, (left, 70), (right, 78), (55, 55, 55), -1)
    cv2.rectangle(frame, (left, 70),
                  (left + round((right - left) * min(1, elapsed / duration)), 78),
                  (85, 205, 155), -1)
    return frame


def summary_frame(width: int, height: int, report: dict, audit: dict) -> np.ndarray:
    frame = np.full((height, width, 3), (19, 22, 20), dtype=np.uint8)
    lines = [
        ("GOLDEN DESKTOP RESULT", 44, 1.0, (245, 245, 240), 2),
        ("6 / 6 exact submissions", 112, .9, (104, 220, 170), 2),
        ("cold  >  reuse  >  reuse  >  repair  >  reuse  >  reuse", 160, .58, (225, 225, 220), 1),
        ("old-layout target pointer admissions     0", 224, .62, (225, 225, 220), 1),
        (f"verified terminal releases               {audit['verified_terminal_releases']} / {audit['terminal_programs']}", 264, .62, (225, 225, 220), 1),
        (f"planner generations / model images       {report['planner_generations_including_preflight']} / {report['model_visible_images']}", 304, .62, (225, 225, 220), 1),
        (f"actual input tokens                       {report['usage']['input_tokens']:,}", 344, .62, (225, 225, 220), 1),
        (f"input to next observation median          {report['input_feedback_median_ms']:.3f} ms", 384, .62, (225, 225, 220), 1),
        ("ONE FRESH PERSISTENT-ONLY RUN  /  NO GENERAL SPEED CLAIM", 458, .52, (165, 165, 160), 1),
    ]
    for text, y, scale, color, thickness in lines:
        cv2.putText(frame, text, (40, y), cv2.FONT_HERSHEY_SIMPLEX,
                    scale, color, thickness, cv2.LINE_AA)
    return frame


def render(source: Path, output: Path, fps: int = 10, speed: float = 2.0) -> dict:
    runtime = source / "arms" / "persistent" / "runtime"
    observations = [row for row in read_lines(runtime / "events.jsonl")
                    if row.get("event") == "observation" and row.get("image")]
    details = json.loads((source / "arms" / "persistent" / "task-details.json").read_text(encoding="utf-8"))
    report = json.loads((source / "golden-report.json").read_text(encoding="utf-8"))
    audit = json.loads((source / "audit.json").read_text(encoding="utf-8"))
    if not report["passed"] or not audit["passed"]:
        raise ValueError("only an independently audited passing run may be rendered")
    stamps = [row["capture_ns"] for row in observations]
    image_paths = [runtime / Path(row["image"]).name for row in observations]
    start, end = stamps[0], stamps[-1]
    duration = (end - start) / 1e9
    first = cv2.imread(str(image_paths[0]), cv2.IMREAD_COLOR)
    if first is None:
        raise FileNotFoundError(image_paths[0])
    width, image_height = 1050, 780
    frame_size = (width, image_height + 92)
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="agent-interface-video-") as temporary:
        intermediate = Path(temporary) / "intermediate.mp4"
        writer = cv2.VideoWriter(str(intermediate), cv2.VideoWriter_fourcc(*"mp4v"),
                                 fps * speed, frame_size)
        if not writer.isOpened():
            raise RuntimeError("OpenCV video writer did not open")
        source_frames = max(1, round(duration * fps))
        cached_path = None
        cached_image = None
        for index in range(source_frames):
            elapsed = index / fps
            timestamp = start + round(elapsed * 1e9)
            observation_index = max(0, bisect.bisect_right(stamps, timestamp) - 1)
            image_path = image_paths[observation_index]
            if image_path != cached_path:
                cached_image = cv2.imread(str(image_path), cv2.IMREAD_COLOR)
                if cached_image is None:
                    raise FileNotFoundError(image_path)
                cached_path = image_path
            image = fit_frame(cached_image, width, image_height)
            task, route, stage = phase_at(details, timestamp)
            writer.write(label_frame(image, elapsed, duration, task, route, stage))
        final = summary_frame(*frame_size, report, audit)
        for _ in range(round(3 * fps * speed)):
            writer.write(final)
        writer.release()
        command = [imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-i", str(intermediate),
                   "-an", "-c:v", "libx264", "-preset", "medium", "-crf", "22",
                   "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(output)]
        completed = subprocess.run(command, capture_output=True, text=True)
        if completed.returncode != 0:
            raise RuntimeError(completed.stderr[-2000:])
    check = cv2.VideoCapture(str(output))
    metadata = {
        "schema": "agent_interface_golden_video_v1",
        "artifact": output.name,
        "source": (source.relative_to(ROOT).as_posix()
                   if source.is_relative_to(ROOT) else str(source)),
        "source_observations": len(observations),
        "source_timeline_seconds": duration,
        "playback_speed": speed,
        "encoded_fps": check.get(cv2.CAP_PROP_FPS),
        "frames": int(check.get(cv2.CAP_PROP_FRAME_COUNT)),
        "width": int(check.get(cv2.CAP_PROP_FRAME_WIDTH)),
        "height": int(check.get(cv2.CAP_PROP_FRAME_HEIGHT)),
        "duration_seconds": (check.get(cv2.CAP_PROP_FRAME_COUNT) /
                             check.get(cv2.CAP_PROP_FPS)),
        "decoder_fourcc": "".join(chr((int(check.get(cv2.CAP_PROP_FOURCC)) >> (8 * i)) & 0xff)
                                  for i in range(4)),
        "representation": "timeline playback from exact retained runtime observations; unchanged intervals hold the latest exact frame",
    }
    ok, _frame = check.read()
    check.release()
    metadata["first_frame_decodes"] = bool(ok)
    metadata["bytes"] = output.stat().st_size
    metadata["sha256"] = hashlib.sha256(output.read_bytes()).hexdigest()
    output.with_suffix(".json").write_text(json.dumps(metadata, indent=2) + "\n",
                                            encoding="utf-8", newline="\n")
    return metadata


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    print(json.dumps(render(args.source.resolve(), args.output.resolve()), indent=2))


if __name__ == "__main__":
    main()
