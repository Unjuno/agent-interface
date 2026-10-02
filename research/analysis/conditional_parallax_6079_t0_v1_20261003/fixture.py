"""Generate the frozen, truth-separated synthetic parallax corpus for #6079."""
from __future__ import annotations

import base64
import hashlib
import json
import math
from pathlib import Path

WIDTH, HEIGHT = 128, 96
FOCAL, CX, CY = 72.0, 64.0, 48.0
RADIUS_WORLD = 0.5
REQUESTED_DX = 0.85
TIMES = (0, 125, 250, 375, 500, 625, 750, 875)
SCHEDULES = (
    (12.0, 10.0, 8.0, 7.0, 6.0, 5.8, 5.6, 5.4),
    (13.0, 10.8, 8.8, 7.2, 6.2, 6.0, 5.8, 5.6),
    (11.5, 9.6, 7.9, 6.8, 5.9, 5.7, 5.5, 5.3),
)
LANDMARKS = (
    (-9.0, 19.0, 20.0), (-6.0, 28.0, 30.0), (-3.0, 22.0, 26.0),
    (2.0, 25.0, 24.0), (5.0, 18.0, 28.0), (8.0, 30.0, 22.0),
    (-10.0, 33.0, 18.0), (-1.0, 35.0, 32.0), (7.0, 34.0, 20.0),
)


def _round_px(value: float) -> int:
    return int(math.floor(value + 0.5))


def _dot(pixels: bytearray, x: int, y: int, value: int) -> None:
    if 0 <= x < WIDTH and 0 <= y < HEIGHT:
        pixels[y * WIDTH + x] = value


def _disc(pixels: bytearray, x: int, y: int, radius: int) -> None:
    for dy in range(-radius, radius + 1):
        for dx in range(-radius, radius + 1):
            if dx * dx + dy * dy <= radius * radius:
                _dot(pixels, x + dx, y + dy, 240)


def render(z: float, camera_x: float, target_mode: str) -> bytes:
    pixels = bytearray(WIDTH * HEIGHT)
    for idx, (world_x, world_y, depth) in enumerate(LANDMARKS):
        u = _round_px(CX + FOCAL * (world_x - camera_x) / depth)
        v = _round_px(CY - FOCAL * world_y / depth)
        _dot(pixels, u, v, 100 + (idx % 3))

    if target_mode == "screen_overlay":
        u = _round_px(CX)
    else:
        u = _round_px(CX - FOCAL * camera_x / z)
    v = _round_px(CY)
    radius = max(1, _round_px(FOCAL * RADIUS_WORLD / z))
    _disc(pixels, u, v, radius)
    header = f"P5\n{WIDTH} {HEIGHT}\n255\n".encode("ascii")
    return header + bytes(pixels)


def _member(schedule: tuple[float, ...], mode: str, actual_dx: float, side: str) -> dict:
    frames = []
    for idx, (time_ms, z) in enumerate(zip(TIMES, schedule, strict=True)):
        camera_x = actual_dx if idx >= 5 else 0.0
        pgm = render(z, camera_x, mode)
        frames.append({
            "t_ms": time_ms,
            "source_binding": {"session": f"opaque-{side}", "viewport_generation": 1},
            "pgm_b64": base64.b64encode(pgm).decode("ascii"),
        })
    return {"member_id": f"opaque-{side}", "frames": frames}


def build() -> tuple[dict, dict]:
    visible_pairs = []
    truth_pairs = []
    serial = 0
    for family in ("screen_overlay", "sham", "world_match"):
        for schedule_index, schedule in enumerate(SCHEDULES):
            serial += 1
            actual_dx = REQUESTED_DX if family != "sham" else 0.0
            if family == "screen_overlay":
                left_mode, right_mode = "rigid", "screen_overlay"
                left_truth, right_truth = "approach_contact", "screen_overlay_no_contact"
            elif family == "sham":
                left_mode, right_mode = "rigid", "screen_overlay"
                left_truth, right_truth = "approach_contact", "screen_overlay_no_contact"
            else:
                left_mode, right_mode = "rigid", "world_match"
                left_truth, right_truth = "approach_contact", "world_anchored_sprite_no_contact"

            pair_id = f"pair-{serial:02d}"
            receipt = {
                "receipt_id": f"probe-{serial:02d}",
                "coordinate_frame": "synthetic-world-x",
                "requested_dx": REQUESTED_DX,
                "actual_dx": actual_dx,
                "event_t_ms": 500,
                "authority": "none",
            }
            visible_pairs.append({
                "pair_id": pair_id,
                "probe_receipt": receipt,
                "members": [
                    _member(schedule, left_mode, actual_dx, f"{serial:02d}-a"),
                    _member(schedule, right_mode, actual_dx, f"{serial:02d}-b"),
                ],
            })
            truth_pairs.append({
                "pair_id": pair_id,
                "family": family,
                "schedule_index": schedule_index,
                "expected_actual_dx": actual_dx,
                "member_truth": [left_truth, right_truth],
                "contact_time_ms": [1000, None],
                "frame_sha256": [
                    [hashlib.sha256(base64.b64decode(frame["pgm_b64"])).hexdigest() for frame in member["frames"]]
                    for member in visible_pairs[-1]["members"]
                ],
                "expected_disposition": {
                    "screen_overlay": "DISTINGUISHED_UNDER_RIGID_OVERLAY_ASSUMPTIONS",
                    "sham": "UNKNOWN",
                    "world_match": "UNKNOWN",
                }[family],
            })
    return ({"schema": "conditional-parallax-input-v1", "pairs": visible_pairs},
            {"schema": "conditional-parallax-truth-v1", "pairs": truth_pairs})


def main() -> None:
    root = Path(__file__).resolve().parent
    visible, truth = build()
    (root / "candidate_input.json").write_text(json.dumps(visible, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    (root / "truth_sidecar.json").write_text(json.dumps(truth, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    print(f"fixtures={len(visible['pairs'])} frames_per_member={len(visible['pairs'][0]['members'][0]['frames'])}")


if __name__ == "__main__":
    main()
