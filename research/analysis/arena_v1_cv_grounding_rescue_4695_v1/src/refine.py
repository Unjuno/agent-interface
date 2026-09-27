#!/usr/bin/env python3
"""Fail-closed orange-square proposal extractor. It grants no input authority."""
from __future__ import annotations

import json
import sys
from pathlib import Path

from PIL import Image

ORANGE = (249, 115, 22)
TOLERANCE = 8
MIN_AREA = 1600
MAX_AREA = 12000
MIN_FILL = 0.86
MIN_ASPECT = 0.84
MAX_ASPECT = 1.19


def matching(pixel: tuple[int, ...]) -> bool:
    return len(pixel) >= 3 and all(abs(pixel[i] - ORANGE[i]) <= TOLERANCE for i in range(3))


def detect(path: Path) -> dict:
    image = Image.open(path).convert("RGB")
    width, height = image.size
    pixels = list(image.getdata())
    seen = bytearray(width * height)
    candidates = []
    for start, pixel in enumerate(pixels):
        if seen[start] or not matching(pixel):
            continue
        seen[start] = 1
        queue = [start]
        head = 0
        xs, ys = [], []
        while head < len(queue):
            index = queue[head]
            head += 1
            x, y = index % width, index // width
            xs.append(x)
            ys.append(y)
            for nxt in (index - 1 if x else -1, index + 1 if x + 1 < width else -1, index - width if y else -1, index + width if y + 1 < height else -1):
                if nxt >= 0 and not seen[nxt] and matching(pixels[nxt]):
                    seen[nxt] = 1
                    queue.append(nxt)
        x0, y0, x1, y1 = min(xs), min(ys), max(xs) + 1, max(ys) + 1
        bw, bh, area = x1 - x0, y1 - y0, len(xs)
        aspect = bw / bh
        fill = area / (bw * bh)
        eligible = MIN_AREA <= area <= MAX_AREA and MIN_ASPECT <= aspect <= MAX_ASPECT and fill >= MIN_FILL
        if eligible:
            candidates.append({"box_xyxy": [x0, y0, x1, y1], "area": area, "aspect": round(aspect, 6), "fill": round(fill, 6)})
    if len(candidates) != 1:
        return {"status": "ABSTAIN", "reason": "no_eligible_component" if not candidates else "multiple_eligible_components", "candidate_count": len(candidates), "candidates": candidates}
    return {"status": "PROPOSAL", "reason": "unique_orange_square_component", "candidate_count": 1, **candidates[0]}


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("usage: refine.py input-dir output.json")
    source, dest = Path(sys.argv[1]), Path(sys.argv[2])
    result = {"rows": [{"id": p.stem, **detect(p)} for p in sorted(source.glob("*.png"))]}
    dest.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"rows": len(result["rows"]), "proposals": sum(r["status"] == "PROPOSAL" for r in result["rows"]), "abstentions": sum(r["status"] == "ABSTAIN" for r in result["rows"])}, indent=2))


if __name__ == "__main__":
    main()
