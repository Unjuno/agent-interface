#!/usr/bin/env python3
"""Build six pixel-identical approach/animation counterfactual pairs."""

from __future__ import annotations

import argparse
import base64
import gzip
import json
from pathlib import Path

WIDTH = 64
HEIGHT = 64
TIMESTAMPS_MS = [0, 100, 200, 300, 400, 500, 600, 700]
CONTACT_MS = [760, 800, 840, 900, 1000, 1200]


def render_disk(radius: float) -> bytes:
    pixels = bytearray(WIDTH * HEIGHT)
    cx = WIDTH / 2
    cy = HEIGHT / 2
    for y in range(HEIGHT):
        for x in range(WIDTH):
            if (x + 0.5 - cx) ** 2 + (y + 0.5 - cy) ** 2 <= radius**2:
                pixels[y * WIDTH + x] = 255
    return f"P5\n{WIDTH} {HEIGHT}\n255\n".encode("ascii") + bytes(pixels)


def build() -> tuple[list[dict], dict]:
    observations: list[dict] = []
    truth: dict = {"pairs": []}
    for index, contact_ms in enumerate(CONTACT_MS, start=1):
        pair_key = f"pair-{index:02d}"
        approach_id = f"case-{index:02d}-a"
        animation_id = f"case-{index:02d}-b"
        frames = []
        for timestamp_ms in TIMESTAMPS_MS:
            radius = 2.0 * contact_ms / (contact_ms - timestamp_ms)
            frames.append(base64.b64encode(render_disk(radius)).decode("ascii"))
        # The candidate-visible records contain no world/contact labels.
        record = {
            "pair_key": pair_key,
            "timestamps_ms": list(TIMESTAMPS_MS),
            "frames_b64": frames,
            "width": WIDTH,
            "height": HEIGHT,
        }
        observations.extend(
            [
                {"case_id": approach_id, **record},
                {"case_id": animation_id, **record},
            ]
        )
        truth["pairs"].append(
            {
                "pair_key": pair_key,
                "approach_case": approach_id,
                "approach_contact_ms": contact_ms,
                "animation_case": animation_id,
                "animation_contact_ms": None,
            }
        )
    return observations, truth


def write_jsonl(path: Path, rows: list[dict]) -> None:
    payload = "".join(
        json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n" for row in rows
    ).encode("utf-8")
    path.write_bytes(gzip.compress(payload, mtime=0))


def construction_check() -> None:
    observations, truth = build()
    assert len(observations) == 12
    assert len(truth["pairs"]) == 6
    by_id = {row["case_id"]: row for row in observations}
    for pair in truth["pairs"]:
        left = by_id[pair["approach_case"]]
        right = by_id[pair["animation_case"]]
        assert left["timestamps_ms"] == right["timestamps_ms"]
        assert left["frames_b64"] == right["frames_b64"]
        assert not ({"world", "contact_ms", "truth"} & left.keys())
        assert len(left["frames_b64"]) == len(TIMESTAMPS_MS)
    assert len({row["frames_b64"][-1] for row in observations[::2]}) > 1


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--construction-check", action="store_true")
    parser.add_argument("--out", type=Path, default=Path("."))
    args = parser.parse_args()
    if args.construction_check:
        construction_check()
        print("construction PASS: 6 exact raster pairs, 12 opaque cases")
        return
    args.out.mkdir(parents=True, exist_ok=True)
    observations, truth = build()
    write_jsonl(args.out / "observer_input.jsonl.gz", observations)
    (args.out / "truth.json").write_text(
        json.dumps(truth, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n"
    )
    print(f"fixture written: {len(observations)} observer records, {len(truth['pairs'])} pairs")


if __name__ == "__main__":
    main()
