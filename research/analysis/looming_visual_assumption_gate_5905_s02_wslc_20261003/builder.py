"""Deterministically render the frozen, finite PGM frame fixture."""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

W = H = 96
CENTER = (48.0, 48.0)
ANCHORS = ((10, 10), (86, 10), (10, 86), (86, 86))


def _canvas():
    return bytearray(W * H)


def _pixel(buf, x, y, value):
    ix, iy = int(round(x)), int(round(y))
    if 0 <= ix < W and 0 <= iy < H:
        buf[iy * W + ix] = value


def _circle(buf, cx, cy, rx, ry, value):
    for y in range(max(0, int(cy - ry - 1)), min(H, int(cy + ry + 2))):
        for x in range(max(0, int(cx - rx - 1)), min(W, int(cx + rx + 2))):
            if ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 <= 1:
                _pixel(buf, x, y, value)


def _square(buf, cx, cy, radius, value):
    for y in range(int(cy - radius), int(cy + radius + 1)):
        for x in range(int(cx - radius), int(cx + radius + 1)):
            _pixel(buf, x, y, value)


def _scene_points(scale):
    points = []
    for ring in (23.0, 29.0, 35.0):
        for degree in range(0, 360, 30):
            angle = math.radians(degree)
            points.append((CENTER[0] + ring * scale * math.cos(angle),
                           CENTER[1] + ring * scale * math.sin(angle)))
    return points


def _frame(target, anchors=True, scene_scale=1.0, target_intensity=220,
           target_center=CENTER, radii=(10.0, 10.0), occlude=False,
           anchor_scale=1.0, unstable_anchor=False):
    buf = _canvas()
    if anchors:
        for i, (x, y) in enumerate(ANCHORS):
            if unstable_anchor and i == 0 and target == 1:
                x += 7
            else:
                x = CENTER[0] + (x - CENTER[0]) * anchor_scale
                y = CENTER[1] + (y - CENTER[1]) * anchor_scale
            _square(buf, x, y, 1, 128)
    for x, y in _scene_points(scene_scale):
        _pixel(buf, x, y, 80)
    cx, cy = target_center
    rx, ry = radii
    _circle(buf, cx, cy, rx, ry, target_intensity)
    if occlude and target == 1:
        # A black rectangle covers the right half, creating an observable silhouette loss.
        for y in range(int(cy - ry - 1), int(cy + ry + 2)):
            for x in range(int(cx), int(cx + rx + 2)):
                _pixel(buf, x, y, 0)
    return bytes(buf)


def _pgm(pixels):
    return b"P5\n96 96\n255\n" + pixels


def build(root: Path):
    images = root / "images"
    images.mkdir(parents=True, exist_ok=True)
    rows = []
    truth = []

    def add(cid, p0, p1, expected, reason, ttc_ms=None, share=None):
        names = (f"{cid}_0.pgm", f"{cid}_1.pgm")
        raw = (_pgm(p0), _pgm(p1))
        for name, data in zip(names, raw):
            (images / name).write_bytes(data)
        rows.append({"case_id": cid, "frame0": f"images/{names[0]}",
                     "frame1": f"images/{names[1]}", "t0_ms": 0,
                     "t1_ms": 100, "source_epoch": "epoch-7"})
        truth.append({"case_id": cid, "expected": expected, "reason": reason,
                      "ttc_ms": ttc_ms, "paired_with": share,
                      "frame_sha256": [hashlib.sha256(x).hexdigest() for x in raw]})

    # Three positive cases have stable anchors and distinguishable multi-feature radial flow.
    for n, (r0, r1) in enumerate(((10.0, 14.0), (10.0, 12.0), (12.0, 14.0)), 1):
        scale = 1.2
        p0 = _frame(0, scene_scale=1.0, radii=(r0, r0))
        p1 = _frame(1, scene_scale=scale, radii=(r1, r1))
        # TTC oracle is based on the exact rasterized target area, independently reproducible.
        a0 = sum(v >= 170 for v in p0)
        a1 = sum(v >= 170 for v in p1)
        q0, q1 = math.sqrt(a0 / math.pi), math.sqrt(a1 / math.pi)
        ttc = round(100 * q0 / (q1 - q0), 6)
        add(f"k{n:02d}", p0, p1, "CUE", "coherent_centered_expansion", ttc)

    # Seven visible/structural controls plus an intentionally non-identifiable pair.
    add("k04", _frame(0, radii=(10, 10)),
        _frame(1, radii=(12, 12), scene_scale=1.15, anchor_scale=1.15),
        "REJECT", "common_mode_zoom")
    add("k05", _frame(0, radii=(10, 10)),
        _frame(1, radii=(14, 14), target_center=(57, 48)),
        "REJECT", "off_axis_motion")
    add("k06", _frame(0, radii=(10, 10)),
        _frame(1, radii=(15, 8)), "REJECT", "shape_deformation")
    add("k07", _frame(0, radii=(10, 10)),
        _frame(1, radii=(14, 14), occlude=True), "REJECT", "partial_occlusion")
    add("k08", _frame(0, radii=(10, 10), target_intensity=220),
        _frame(1, radii=(14, 14), target_intensity=180),
        "REJECT", "appearance_discontinuity")
    add("k09", _frame(0, anchors=False, radii=(10, 10)),
        _frame(1, anchors=False, radii=(14, 14)), "UNKNOWN", "missing_anchors")
    add("k10", _frame(0, radii=(10, 10)),
        _frame(1, radii=(14, 14), unstable_anchor=True),
        "UNKNOWN", "unstable_anchors")

    pair0 = _frame(0, radii=(10, 10))
    pair1 = _frame(1, radii=(14, 14))
    add("k11", pair0, pair1, "UNKNOWN", "insufficient_scene_flow", share="k12")
    add("k12", pair0, pair1, "UNKNOWN", "insufficient_scene_flow", share="k11")

    fixture = {"schema": "looming-image-only-s02-v1", "width": W, "height": H,
               "epoch": "epoch-7", "cases": rows}
    oracle = {"schema": "looming-image-only-oracle-s02-v1", "cases": truth,
              "positive_ttc_error_fraction_max": 0.05,
              "release_lead_ms_min": 200.0, "release_lead_ms_max": 900.0,
              "frame_identical_pair": ["k11", "k12"]}
    (root / "fixture.json").write_text(json.dumps(fixture, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    (root / "oracle.json").write_text(json.dumps(oracle, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return fixture, oracle


if __name__ == "__main__":
    import sys
    build(Path(sys.argv[1]))
