#!/usr/bin/env python3
"""Build deterministic RGB8 fixtures for the Issue #1998 A03 construction."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
WIDTH, HEIGHT = 128, 96


def make_frame(kind: str) -> bytes:
    pixels = bytearray(WIDTH * HEIGHT * 3)

    def put(x: int, y: int, rgb: tuple[int, int, int]) -> None:
        off = (y * WIDTH + x) * 3
        pixels[off:off + 3] = bytes(rgb)

    if kind == "flat_ui":
        pixels[:] = bytes((238, 241, 244)) * (WIDTH * HEIGHT)
        for y in range(8, 88):
            for x in range(8, 120):
                if x < 28 or y < 22:
                    put(x, y, (211, 220, 228))
        for i in range(8):
            x0, y0 = 36, 28 + i * 7
            for y in range(y0, min(y0 + 3, HEIGHT)):
                for x in range(x0, x0 + 76 - (i % 3) * 8):
                    put(x, y, (35 + i * 12, 82 + i * 7, 142 + i * 5))
    elif kind == "structured_edges":
        for y in range(HEIGHT):
            for x in range(WIDTH):
                if x in (0, 1, 126, 127) or y in (0, 1, 94, 95):
                    color = (12, 18, 24)
                elif (x // 16 + y // 12) % 2:
                    color = (226, 230, 235)
                else:
                    color = (244, 246, 248)
                put(x, y, color)
        for y in range(18, 78, 6):
            for x in range(22, 108):
                if x % 11 not in (0, 1, 2):
                    put(x, y, (18, 98, 171))
    elif kind == "seeded_high_entropy":
        state = 0x1998A03
        for i in range(WIDTH * HEIGHT * 3):
            state = (1664525 * state + 1013904223) & 0xFFFFFFFF
            pixels[i] = (state >> 16) & 0xFF
    else:
        raise ValueError(kind)
    return bytes(pixels)


def main() -> None:
    source = ROOT / "source"
    source.mkdir(exist_ok=True)
    kinds = ("flat_ui", "structured_edges", "seeded_high_entropy")
    for kind in kinds:
        (source / f"{kind}.rgb8").write_bytes(make_frame(kind))
    design = {
        "schema": "1998-a03-design-v1",
        "width": WIDTH,
        "height": HEIGHT,
        "channels": 3,
        "encoding": "RGB8",
        "frames": [
            {"frame_id": f"frame-{kind}", "epoch": 7, "pattern": kind,
             "source": f"source/{kind}.rgb8"}
            for kind in kinds
        ],
        "valid_rois": [
            {"roi_id": "tiny", "bounds": [0, 0, 16, 16]},
            {"roi_id": "small", "bounds": [16, 16, 48, 40]},
            {"roi_id": "medium", "bounds": [32, 24, 96, 72]},
            {"roi_id": "large", "bounds": [0, 0, 120, 88]},
            {"roi_id": "full_frame", "bounds": [0, 0, 128, 96]},
            {"roi_id": "narrow_tall", "bounds": [60, 0, 68, 96]},
        ],
        "invalid_requests": [
            {"case_id": "invalid-stale-epoch", "reason": "uncertain",
             "frame_id": "frame-flat_ui", "epoch": 6, "focus_state": "active",
             "region_id": "roi-invalid", "candidate_region_ids": ["roi-invalid"],
             "bounds": [0, 0, 16, 16]},
            {"case_id": "invalid-replaced-identity", "reason": "uncertain",
             "frame_id": "replaced-frame", "epoch": 7, "focus_state": "active",
             "region_id": "roi-invalid", "candidate_region_ids": ["roi-invalid"],
             "bounds": [0, 0, 16, 16]},
            {"case_id": "invalid-focus-lost", "reason": "uncertain",
             "frame_id": "frame-flat_ui", "epoch": 7, "focus_state": "lost",
             "region_id": "roi-invalid", "candidate_region_ids": ["roi-invalid"],
             "bounds": [0, 0, 16, 16]},
            {"case_id": "invalid-ambiguous", "reason": "uncertain",
             "frame_id": "frame-flat_ui", "epoch": 7, "focus_state": "active",
             "region_id": "roi-invalid", "candidate_region_ids": ["roi-invalid", "roi-other"],
             "bounds": [0, 0, 16, 16]},
            {"case_id": "invalid-out-of-bounds", "reason": "uncertain",
             "frame_id": "frame-flat_ui", "epoch": 7, "focus_state": "active",
             "region_id": "roi-invalid", "candidate_region_ids": ["roi-invalid"],
             "bounds": [120, 80, 136, 96]},
        ],
    }
    (ROOT / "design.json").write_text(json.dumps(design, sort_keys=True, indent=2) + "\n")


if __name__ == "__main__":
    main()
