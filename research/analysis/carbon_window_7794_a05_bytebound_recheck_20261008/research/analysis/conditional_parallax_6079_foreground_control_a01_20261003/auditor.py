"""Independent raw-only audit of the #6079 foreground control."""
from __future__ import annotations

import base64
import json
import sys
from pathlib import Path

TARGET = 240
LANDMARKS = {100, 101, 102}


def pixels(frame: dict) -> tuple[int, int, bytes]:
    raw = base64.b64decode(frame["pgm_b64"], validate=True)
    magic, dims, maximum, data = raw.split(b"\n", 3)
    if magic != b"P5" or maximum != b"255":
        raise ValueError("invalid PGM source")
    width, height = map(int, dims.split())
    if len(data) != width * height:
        raise ValueError("invalid PGM dimensions")
    return width, height, data


def centroid(points: list[int], width: int) -> tuple[float, float]:
    return sum(i % width for i in points) / len(points), sum(i // width for i in points) / len(points)


def inspect(path: Path, output_path: Path) -> dict:
    source = json.loads(path.read_text())
    parent_path = path.parent.parent / "conditional_parallax_6079_t0_v1_20261003" / "candidate_input.json"
    parent = json.loads(parent_path.read_text())
    baseline = parent["pairs"][3]
    pair = source["pairs"][0]
    lframes, rframes = pair["members"][0]["frames"], pair["members"][1]["frames"]
    base_right = baseline["members"][1]["frames"]
    passive_equal = all(a["pgm_b64"] == b["pgm_b64"] for a, b in zip(lframes[:5], rframes[:5], strict=True))
    target_unchanged = True
    target_separations = []
    landmark_separations = []
    for idx in range(5, 8):
        lw, lh, lp = pixels(lframes[idx])
        rw, rh, rp = pixels(rframes[idx])
        bw, bh, bp = pixels(base_right[idx])
        if (lw, lh) != (rw, rh) or (rw, rh) != (bw, bh):
            raise ValueError("paired raster geometry differs")
        lt = [i for i, v in enumerate(lp) if v == TARGET]
        rt = [i for i, v in enumerate(rp) if v == TARGET]
        bt = [i for i, v in enumerate(bp) if v == TARGET]
        target_unchanged &= lt == rt == bt
        target_separations.append(((centroid(lt, lw)[0] - centroid(rt, rw)[0]) ** 2 + (centroid(lt, lw)[1] - centroid(rt, rw)[1]) ** 2) ** 0.5)
        lb = [i for i, v in enumerate(lp) if v in LANDMARKS]
        rb = [i for i, v in enumerate(rp) if v in LANDMARKS]
        dx = centroid(lt, lw)[0] - centroid(lb, lw)[0] - (centroid(rt, rw)[0] - centroid(rb, rw)[0])
        dy = centroid(lt, lw)[1] - centroid(lb, lw)[1] - (centroid(rt, rw)[1] - centroid(rb, rw)[1])
        landmark_separations.append((dx * dx + dy * dy) ** 0.5)
    candidate = json.loads(output_path.read_text())
    result = candidate["results"][0]
    return {
        "schema": "conditional-parallax-foreground-audit-v1",
        "passive_frames_identical": passive_equal,
        "target_pixels_unchanged": target_unchanged,
        "target_separation_px": target_separations,
        "candidate_landmark_separation_px": landmark_separations,
        "candidate_classification": result["classification"],
        "candidate_false_distinction": target_unchanged and result["classification"].startswith("DISTINGUISHED"),
        "disposition": "CONTROL_EXPOSED" if target_unchanged and result["classification"].startswith("DISTINGUISHED") else "CONTROL_HELD",
    }


if __name__ == "__main__":
    result = inspect(Path(sys.argv[1]), Path(sys.argv[2]))
    Path(sys.argv[3]).write_text(json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n")
    print(f"disposition={result['disposition']} target_pixels_unchanged={result['target_pixels_unchanged']}")
