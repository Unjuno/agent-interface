#!/usr/bin/env python3
"""Image-and-time-only cue candidate; it never reads auditor truth labels."""

from __future__ import annotations

import argparse
import base64
import gzip
import hashlib
import json
import math
from pathlib import Path

YIELD_HORIZON_MS = 350.0
ENDPOINT_GROWTH_RATIO = 2.0


def decode_pgm(encoded: str, width: int, height: int) -> bytes:
    data = base64.b64decode(encoded, validate=True)
    header, w_h, maxval, pixels = data.split(b"\n", 3)
    if header != b"P5" or w_h != f"{width} {height}".encode() or maxval != b"255":
        raise ValueError("unexpected PGM header")
    if len(pixels) != width * height:
        raise ValueError("unexpected PGM pixel length")
    return pixels


def digest_record(record: dict) -> str:
    payload = json.dumps(record, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def evaluate(record: dict) -> dict:
    required = {"case_id", "pair_key", "timestamps_ms", "frames_b64", "width", "height"}
    if set(record) != required:
        raise ValueError("candidate input schema mismatch")
    times = record["timestamps_ms"]
    frames = [decode_pgm(x, record["width"], record["height"]) for x in record["frames_b64"]]
    if len(frames) != len(times) or len(times) < 2 or sorted(times) != times:
        raise ValueError("invalid time/frame sequence")
    areas = [sum(pixel != 0 for pixel in frame) for frame in frames]
    radii = [math.sqrt(area / math.pi) for area in areas]
    changed = sum(a != b for a, b in zip(frames, frames[1:]))
    growth = radii[-1] / radii[0] if radii[0] else math.inf
    dt = times[-1] - times[-2]
    slope = (radii[-1] - radii[-2]) / dt if dt > 0 else 0.0
    tau = radii[-1] / slope if slope > 0 else None
    cues = {
        "any_pixel_change": "YIELD" if changed else "CONTINUE",
        "endpoint_radius_growth": "YIELD" if growth >= ENDPOINT_GROWTH_RATIO else "CONTINUE",
        "radius_tau": "UNKNOWN" if tau is None else ("YIELD" if tau <= YIELD_HORIZON_MS else "CONTINUE"),
    }
    return {
        "case_id": record["case_id"],
        "pair_key": record["pair_key"],
        "observer_input_sha256": digest_record(record),
        "frame_count": len(frames),
        "pixel_change_intervals": changed,
        "radius_start_px": radii[0],
        "radius_end_px": radii[-1],
        "estimated_tau_ms": tau,
        "cues": cues,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    with gzip.open(args.input, "rt", encoding="utf-8") as stream:
        records = [json.loads(line) for line in stream if line.strip()]
    results = [evaluate(record) for record in records]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        "".join(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n" for row in results),
        encoding="utf-8",
        newline="\n",
    )
    print(f"candidate complete: {len(results)} records")


if __name__ == "__main__":
    main()
