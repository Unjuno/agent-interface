#!/usr/bin/env python3
"""Summarize the frozen health-ROI pixels from the retained Astra video."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

HERE = Path(__file__).resolve().parent
INPUT = HERE / "input/health_roi.rgb"
OUT = Path(os.environ.get("RESULT_DIR", HERE / "results/a01")) / "candidate.raw.json"
FRAME_COUNT = 60
FRAME_BYTES = 72 * 48 * 3
PLAYBACK_START_S = 22.3
PLAYBACK_FPS = 10.0
MEAN_CHANGED_AT = 4.0


def ensure_output_is_new(path: Path) -> None:
    if path.exists():
        raise FileExistsError(f"refusing to overwrite retained output: {path}")


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def mean_abs(a: bytes, b: bytes) -> float:
    return sum(abs(x - y) for x, y in zip(a, b)) / len(a)


def main() -> None:
    ensure_output_is_new(OUT)
    raw = INPUT.read_bytes()
    assert len(raw) == FRAME_COUNT * FRAME_BYTES, "unexpected frozen ROI frame count/shape"
    frames = [raw[i * FRAME_BYTES : (i + 1) * FRAME_BYTES] for i in range(FRAME_COUNT)]
    baseline = frames[0]
    rows = []
    for i, frame in enumerate(frames):
        playback_s = PLAYBACK_START_S + i / PLAYBACK_FPS
        mae = mean_abs(frame, baseline)
        rows.append(
            {
                "frame_index": i,
                "playback_seconds": round(playback_s, 1),
                "game_seconds": round(playback_s * 2, 1),
                "health_roi_sha256": sha(frame),
                "mean_absolute_rgb_delta_from_wait_start": round(mae, 6),
                "pixel_state": "CHANGED_FROM_WAIT_START" if mae > MEAN_CHANGED_AT else "BASELINE_MATCH",
            }
        )
    changed = [x for x in rows if x["pixel_state"] == "CHANGED_FROM_WAIT_START"]
    first = changed[0] if changed else None
    result = {
        "schema": "map01-astra-decision4-dense-health-roi-replay-v1",
        "run_id": "MAP01-ASTRA-WAIT-HUD-REPLAY-A01-20261005",
        "status": "PASS_DESCRIPTIVE_VIDEO_FRAME_BOUNDARY_RECONSTRUCTION" if first else "HOLD_NO_HEALTH_PIXEL_CHANGE_FOUND",
        "input_sha256": sha(raw),
        "frame_count": FRAME_COUNT,
        "roi": {"x": 128, "y": 486, "width": 72, "height": 48, "pixel_format": "rgb24"},
        "sampling": {"playback_start_seconds": PLAYBACK_START_S, "fps": PLAYBACK_FPS, "playback_speed": 2.0, "game_seconds_per_frame": 0.2},
        "health_state_threshold_mean_abs_rgb_delta": MEAN_CHANGED_AT,
        "baseline_health_visual_read": 100,
        "first_changed_frame": first,
        "last_baseline_frame": rows[changed[0]["frame_index"] - 1] if first and first["frame_index"] else None,
        "max_mae_before_first_change": max(x["mean_absolute_rgb_delta_from_wait_start"] for x in rows[: first["frame_index"]]) if first else None,
        "rows": rows,
        "scope": "Posthoc pixel-state scan of the retained 2x video; values and phase labels are separately transcribed from selected full-frame stills.",
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("x", encoding="utf-8") as output:
        output.write(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({k: result[k] for k in ("status", "frame_count", "first_changed_frame", "last_baseline_frame", "input_sha256")}, sort_keys=True))


if __name__ == "__main__":
    main()
