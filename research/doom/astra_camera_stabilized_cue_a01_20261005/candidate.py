#!/usr/bin/env python3
"""One-shot registered-vs-unregistered warm-pixel transition diagnostic."""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import numpy as np

START_S = 21.5
END_S = 23.5
FPS = 5
WIDTH = 320
HEIGHT = 280
MAX_SHIFT = 16
WARM_THRESHOLD = 40
VIDEO_SHA256 = "201ab6aaa8ab5823285b44864ad1df899ebe5a19c97ec6e84b8cc5db063f6be4"
REFERENCE_A01_RAW_SHA256 = "b6fee496a45ec9d88a6d50b060cbfef2c781fa8d44020d80542b9ba8f77a9e27"


def warm_mask(frame):
    rgb = frame.astype(np.int16)
    red, green, blue = rgb[:, :, 0], rgb[:, :, 1], rgb[:, :, 2]
    mask = ((red >= 170) & (green >= 45) & (green <= 190) &
            (blue <= 95) & (red >= green * 1.25))
    mask[30:230, :] &= True
    outside = np.ones(mask.shape, dtype=bool)
    outside[30:230, :] = False
    mask[outside] = False
    mask[145:230, 130:190] = False
    return mask


def gray(frame):
    # Integer luma is adequate for robust global translation registration.
    x = frame.astype(np.uint16)
    return ((77 * x[:, :, 0] + 150 * x[:, :, 1] + 29 * x[:, :, 2]) >> 8)


def overlap_slices(height, width, dy, dx):
    py0, py1 = max(0, -dy), min(height, height - dy)
    px0, px1 = max(0, -dx), min(width, width - dx)
    cy0, cy1 = py0 + dy, py1 + dy
    cx0, cx1 = px0 + dx, px1 + dx
    return (slice(py0, py1), slice(px0, px1),
            slice(cy0, cy1), slice(cx0, cx1))


def estimate_shift(previous_gray, current_gray):
    """Return the integer translation moving prior scene coordinates to current."""
    h, w = current_gray.shape
    scene = np.zeros((h, w), dtype=bool)
    scene[30:230, :] = True
    scene[145:230, 130:190] = False
    scene[96:105, 156:165] = False  # omit the static center reticle
    best = None
    for dy in range(-MAX_SHIFT, MAX_SHIFT + 1):
        for dx in range(-MAX_SHIFT, MAX_SHIFT + 1):
            py, px, cy, cx = overlap_slices(h, w, dy, dx)
            valid = scene[cy, cx]
            if int(valid.sum()) < 1000:
                continue
            delta = np.abs(previous_gray[py, px].astype(np.int16) -
                           current_gray[cy, cx].astype(np.int16))
            score = float(np.median(delta[valid]))
            tie = (round(score, 6), abs(dx) + abs(dy), abs(dy), dy, dx)
            if best is None or tie < best[0]:
                best = (tie, dx, dy, score)
    if best is None:
        raise ValueError("no_registration_overlap")
    _, dx, dy, score = best
    return dx, dy, score


def translated_previous(mask, dx, dy):
    h, w = mask.shape
    result = np.zeros_like(mask)
    py, px, cy, cx = overlap_slices(h, w, dy, dx)
    result[cy, cx] = mask[py, px]
    return result


def main(video, output_dir):
    video = Path(video)
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    video_hash = hashlib.sha256(video.read_bytes()).hexdigest()
    if video_hash != VIDEO_SHA256:
        raise SystemExit("STOP_SOURCE_VIDEO_HASH_MISMATCH")
    command = [
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-ss", str(START_S),
        "-i", str(video), "-t", str(END_S - START_S), "-vf",
        f"fps={FPS},scale={WIDTH}:{HEIGHT}", "-f", "rawvideo",
        "-pix_fmt", "rgb24", "pipe:1",
    ]
    decoded = subprocess.run(command, check=True, stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
    frame_size = WIDTH * HEIGHT * 3
    if len(decoded.stdout) % frame_size:
        raise SystemExit("STOP_PARTIAL_FRAME_STREAM")
    frames = np.frombuffer(decoded.stdout, dtype=np.uint8).reshape(
        (-1, HEIGHT, WIDTH, 3))
    if len(frames) != 10:
        raise SystemExit(f"STOP_FRAME_COUNT:{len(frames)}")
    input_path = out / "frames.rgb"
    input_path.write_bytes(decoded.stdout)
    rows = []
    previous_gray = previous_warm = None
    for i, frame in enumerate(frames):
        current_gray = gray(frame)
        current_warm = warm_mask(frame)
        if previous_gray is None:
            dx = dy = None
            score = None
            unregistered = registered = int(current_warm.sum())
        else:
            dx, dy, score = estimate_shift(previous_gray, current_gray)
            unregistered = int((current_warm & ~previous_warm).sum())
            aligned = translated_previous(previous_warm, dx, dy)
            registered = int((current_warm & ~aligned).sum())
        rows.append({
            "frame": i,
            "video_time_s": round(START_S + i / FPS, 3),
            "estimated_shift_current_vs_previous_px": None if dx is None else [dx, dy],
            "registration_median_luma_error": score,
            "new_warm_pixels_unregistered": unregistered,
            "new_warm_pixels_registered": registered,
            "trigger_unregistered": bool(i > 0 and unregistered >= WARM_THRESHOLD),
            "trigger_registered": bool(i > 0 and registered >= WARM_THRESHOLD),
        })
        previous_gray, previous_warm = current_gray, current_warm
    raw = {
        "format": "astra_camera_stabilized_cue_a01_v1",
        "video_sha256": video_hash,
        "reference_a01_raw_sha256": REFERENCE_A01_RAW_SHA256,
        "ffmpeg_command": command,
        "frame_count": len(frames),
        "frame_size_bytes": len(decoded.stdout),
        "frames_rgb_sha256": hashlib.sha256(decoded.stdout).hexdigest(),
        "parameters": {"fps": FPS, "width": WIDTH, "height": HEIGHT,
                        "max_shift_px": MAX_SHIFT,
                        "warm_pixel_threshold": WARM_THRESHOLD},
        "rows": rows,
    }
    (out / "raw.json").write_text(json.dumps(raw, indent=2) + "\n")
    print(json.dumps({
        "frames": len(rows),
        "wall_window": next((r for r in rows if r["video_time_s"] == 22.7), None),
        "warm_cue_counts": [{"t": r["video_time_s"],
                             "raw": r["new_warm_pixels_unregistered"],
                             "registered": r["new_warm_pixels_registered"]}
                            for r in rows[1:]],
        "frames_rgb_sha256": raw["frames_rgb_sha256"],
    }, indent=2))


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("usage: candidate.py VIDEO OUTPUT_DIR")
    main(sys.argv[1], sys.argv[2])
