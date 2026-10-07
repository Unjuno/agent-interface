#!/usr/bin/env python3
"""Independent reconstruction of A01's registered cue from retained RGB frames."""
import hashlib
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent
RAW_PATH = ROOT / "raw.json"
FRAME_PATH = ROOT / "frames.rgb"
EXPECTED_VIDEO = "201ab6aaa8ab5823285b44864ad1df899ebe5a19c97ec6e84b8cc5db063f6be4"
EXPECTED_REFERENCE_RAW = "b6fee496a45ec9d88a6d50b060cbfef2c781fa8d44020d80542b9ba8f77a9e27"
REFERENCE_UNREGISTERED = [4, 15, 96, 0, 0, 0, 186, 213, 176, 57]


def to_gray(frame):
    pixels = frame.astype(np.uint32)
    return ((77 * pixels[:, :, 0] + 150 * pixels[:, :, 1] +
             29 * pixels[:, :, 2]) >> 8).astype(np.uint16)


def luma_shift(prior, current, limit):
    """Cross-correlation-style independent wrap-safe translation search."""
    height, width = current.shape
    use = np.zeros((height, width), dtype=bool)
    use[30:230, :] = True
    use[145:230, 130:190] = False
    use[96:105, 156:165] = False
    options = []
    for dy in range(-limit, limit + 1):
        for dx in range(-limit, limit + 1):
            # Rolling is convenient here; erase the wrapped margins before scoring.
            rolled = np.roll(prior, shift=(dy, dx), axis=(0, 1))
            valid = use.copy()
            if dy > 0:
                valid[:dy, :] = False
            elif dy < 0:
                valid[dy:, :] = False
            if dx > 0:
                valid[:, :dx] = False
            elif dx < 0:
                valid[:, dx:] = False
            if int(valid.sum()) < 1000:
                continue
            score = float(np.median(np.abs(
                rolled[valid].astype(np.int32) - current[valid].astype(np.int32))))
            options.append(((round(score, 6), abs(dx) + abs(dy),
                             abs(dy), dy, dx), dx, dy, score))
    if not options:
        raise ValueError("no registration samples")
    _, dx, dy, score = min(options, key=lambda row: row[0])
    return dx, dy, score


def move_mask(mask, dx, dy):
    height, width = mask.shape
    shifted = np.roll(mask, shift=(dy, dx), axis=(0, 1))
    valid = np.ones((height, width), dtype=bool)
    if dy > 0:
        valid[:dy, :] = False
    elif dy < 0:
        valid[dy:, :] = False
    if dx > 0:
        valid[:, :dx] = False
    elif dx < 0:
        valid[:, dx:] = False
    shifted &= valid
    return shifted


def main():
    raw = json.loads(RAW_PATH.read_text())
    errors = []
    frame_bytes = FRAME_PATH.read_bytes()
    digest = hashlib.sha256(frame_bytes).hexdigest()
    width, height = raw["parameters"]["width"], raw["parameters"]["height"]
    expected_size = raw["frame_count"] * width * height * 3
    if digest != raw.get("frames_rgb_sha256"):
        errors.append("frames_digest")
    if len(frame_bytes) != expected_size or expected_size != raw.get("frame_size_bytes"):
        errors.append("frame_size")
    if raw.get("video_sha256") != EXPECTED_VIDEO:
        errors.append("source_video")
    if raw.get("reference_a01_raw_sha256") != EXPECTED_REFERENCE_RAW:
        errors.append("reference_raw")
    if raw.get("frame_count") != 10 or len(raw.get("rows", [])) != 10:
        errors.append("row_count")
    if errors:
        result = {"status": "FAIL_RAW_RECONSTRUCTION", "errors": errors}
        (ROOT / "AUDIT.json").write_text(json.dumps(result, indent=2) + "\n")
        print(json.dumps(result, indent=2))
        raise SystemExit(1)

    frames = np.frombuffer(frame_bytes, dtype=np.uint8).reshape(
        (10, height, width, 3))
    rows = []
    old_warm = old_gray = None
    for i, frame in enumerate(frames):
        channels = frame.astype(np.int32)
        red, green, blue = channels[:, :, 0], channels[:, :, 1], channels[:, :, 2]
        warm = ((red >= 170) & (green >= 45) & (green <= 190) &
                (blue <= 95) & (red >= green * 1.25))
        region = np.zeros(warm.shape, dtype=bool)
        region[30:230, :] = True
        region[145:230, 130:190] = False
        warm &= region
        current_gray = to_gray(frame)
        if i == 0:
            dx = dy = None
            score = None
            plain = registered = int(warm.sum())
        else:
            dx, dy, score = luma_shift(old_gray, current_gray,
                                       raw["parameters"]["max_shift_px"])
            plain = int(np.count_nonzero(warm & ~old_warm))
            registered = int(np.count_nonzero(warm & ~move_mask(old_warm, dx, dy)))
        row = {
            "frame": i,
            "estimated_shift_current_vs_previous_px": None if dx is None else [dx, dy],
            "registration_median_luma_error": score,
            "new_warm_pixels_unregistered": plain,
            "new_warm_pixels_registered": registered,
            "trigger_unregistered": bool(i > 0 and plain >= 40),
            "trigger_registered": bool(i > 0 and registered >= 40),
        }
        if row != raw["rows"][i] and set(row) - {"video_time_s"}:
            # Timestamps are immutable data too; checked separately below.
            checked = dict(raw["rows"][i])
            checked.pop("video_time_s", None)
            if row != checked:
                errors.append(f"row_{i}")
        expected_time = round(21.5 + i * 0.2, 3)
        if raw["rows"][i].get("video_time_s") != expected_time:
            errors.append(f"timestamp_{i}")
        rows.append(row)
        old_warm, old_gray = warm, current_gray

    if [row["new_warm_pixels_unregistered"] for row in rows] != REFERENCE_UNREGISTERED:
        errors.append("paired_control_diverged_from_a01")
    wall = rows[6]
    wall_shift = wall["estimated_shift_current_vs_previous_px"]
    at_boundary = wall_shift is not None and max(abs(wall_shift[0]), abs(wall_shift[1])) >= 16
    if at_boundary:
        disposition = "HOLD_SHIFT_AT_SEARCH_BOUNDARY"
    elif wall["trigger_unregistered"] and not wall["trigger_registered"]:
        disposition = "SUPPRESSED_REFERENCE_WALL_CUE"
    else:
        disposition = "FAIL_WALL_CUE_NOT_SUPPRESSED"
    result = {
        "status": "PASS_RAW_RECONSTRUCTION" if not errors else "FAIL_RAW_RECONSTRUCTION",
        "errors": errors,
        "row_count": len(rows),
        "video_sha256": raw["video_sha256"],
        "frames_rgb_sha256": digest,
        "wall_sample": {"video_time_s": raw["rows"][6]["video_time_s"], **wall},
        "pre_window_muzzle_control": rows[2],
        "disposition": disposition,
        "scope": "arithmetic reconstruction and one reference-frame cue suppression only; no enemy classification or controller effect",
    }
    (ROOT / "AUDIT.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
