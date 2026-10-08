#!/usr/bin/env python3
"""Build the frozen 12-row PGM fixture and opaque candidate input."""
from __future__ import annotations

import hashlib
import json
import math
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parent
W = H = 128
ANCHORS = [(8, 8), (120, 8), (8, 120), (120, 120)]
ASYM = [(0, 12), (35, 15), (88, 17), (143, 11), (203, 18), (247, 13), (311, 16)]
SYM = [(0, 0), (0, 15), (180, 15), (60, 17), (240, 17),
       (120, 13), (300, 13)]


def pgm(points: list[tuple[int, int, int]]) -> bytes:
    data = bytearray(W * H)
    for x, y, radius in points:
        for yy in range(max(0, y - radius), min(H, y + radius + 1)):
            for xx in range(max(0, x - radius), min(W, x + radius + 1)):
                data[yy * W + xx] = 255
    return f"P5\n{W} {H}\n255\n".encode() + data


def photometric(blob: bytes, background: int, foreground: int) -> bytes:
    header, pixels = blob.split(b"255\n", 1)
    mapped = bytes(foreground if p >= 128 else background for p in pixels)
    return header + b"255\n" + mapped


def scene(scale: float = 1.0, pattern=ASYM, *, shift=(0, 0),
          anchor_scale: float = 1.0, target_radii=None, omit=(),
          appearance=False, no_anchors=False, anchor_shift=(0, 0)) -> bytes:
    points = []
    tx, ty = shift
    for i, (deg, radius) in enumerate(pattern):
        if i in omit:
            continue
        a = math.radians(deg)
        x = round(64 + tx + math.cos(a) * radius * scale)
        y = round(64 + ty + math.sin(a) * radius * scale)
        size = 2 if target_radii is None else target_radii[i]
        if appearance:
            x = round(64 + tx + math.cos(a + math.radians(72)) * (radius + 14))
            y = round(64 + ty + math.sin(a + math.radians(72)) * (radius + 14))
        points.append((x, y, size))
    if not no_anchors:
        for x, y in ANCHORS:
            x = round(64 + (x - 64) * anchor_scale + anchor_shift[0])
            y = round(64 + (y - 64) * anchor_scale + anchor_shift[1])
            points.append((x, y, 3))
    return pgm(points)


def write_frame(rel: str, blob: bytes) -> str:
    p = ROOT / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(blob)
    return hashlib.sha256(blob).hexdigest()


def main() -> None:
    rows = []

    def add(name, label, first, second, expected, scale=None):
        variants = (("native", 0, 255), ("low_contrast", 32, 224),
                    ("near_threshold", 127, 129))
        for variant, background, foreground in variants:
            a = first if variant == "native" else photometric(first, background, foreground)
            b = second if variant == "native" else photometric(second, background, foreground)
            opaque = hashlib.sha256(f"6808-S04-row-{len(rows):03d}".encode()).hexdigest()[:16]
            f0, f1 = f"frames/{opaque}-0.pgm", f"frames/{opaque}-1.pgm"
            h0, h1 = write_frame(f0, a), write_frame(f1, b)
            rows.append({"opaque_id": opaque,
                         "family_id": name, "variant": variant,
                         "frame0": f0, "frame1": f1, "sha256": [h0, h1],
                         "t": [0.0, 0.1], "epoch": "epoch-01",
                         "truth": label, "expected": expected, "scale": scale})

    for i, s in enumerate((1.40, 1.50, 1.60), 1):
        add(f"approach-{i}", "eligible_approach", scene(), scene(s),
            "CUE", s)
    add("common-zoom", "common_mode_zoom", scene(),
        scene(1.5, anchor_scale=1.5), "REJECT")
    add("lateral", "lateral_passage", scene(), scene(1.5, shift=(9, 0)), "REJECT")
    add("deformation", "visible_shape_deformation", scene(),
        scene(1.5, target_radii=[1, 3, 1, 3, 1, 3, 1]), "REJECT")
    add("occlusion", "partial_occlusion", scene(),
        scene(1.5, omit=(1, 3, 5)), "REJECT")
    add("appearance", "appearance_discontinuity", scene(),
        scene(1.5, appearance=True), "REJECT")
    add("missing-anchors", "missing_anchors", scene(),
        scene(1.5, no_anchors=True), "UNKNOWN")
    add("unstable-anchors", "unstable_anchors", scene(),
        scene(1.5, anchor_shift=(5, -4)), "REJECT")
    pair0, pair1 = scene(pattern=SYM), scene(1.5, pattern=SYM)
    add("ambiguous-approach", "pixel_indistinguishable_approach", pair0, pair1, "UNKNOWN")
    add("ambiguous-growth", "pixel_indistinguishable_rigid_growth", pair0, pair1, "UNKNOWN")

    truth = {"schema": "looming-contrast-fixture-v1", "width": W, "height": H,
             "rows": rows}
    (ROOT / "truth.json").write_text(json.dumps(truth, indent=2) + "\n")
    public = [{k: row[k] for k in ("opaque_id", "frame0", "frame1", "t", "epoch")}
              for row in rows]
    random.Random("6808-S04-order-v1").shuffle(public)
    (ROOT / "candidate_input.json").write_text(
        json.dumps({"schema": "looming-contrast-input-v1", "rows": public}, indent=2) + "\n")


if __name__ == "__main__":
    main()
