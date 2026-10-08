#!/usr/bin/env python3
"""Image-only candidate: pixel template, one threshold, threshold persistence."""
import json
import os
from collections import deque
from pathlib import Path

ROOT = Path(__file__).parent
OUT_DIR = Path(os.environ.get("OUT_DIR", ROOT))
THRESHOLDS = (64, 128, 192, 240)


def connected(pixels, threshold):
    h, w = len(pixels), len(pixels[0])
    start, goal = (0, 4), (8, 4)
    if pixels[start[1]][start[0]] <= threshold:
        return False
    todo = deque([start])
    seen = {start}
    while todo:
        x, y = todo.popleft()
        if (x, y) == goal:
            return True
        for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
            if 0 <= nx < w and 0 <= ny < h and (nx, ny) not in seen and pixels[ny][nx] > threshold:
                seen.add((nx, ny))
                todo.append((nx, ny))
    return False


def label_pixel_template(pixels, template):
    distance = sum(abs(a - b) for row, ref in zip(pixels, template) for a, b in zip(row, ref)) / (255 * 81)
    if distance <= 0.02:
        return "PRESENT"
    if distance >= 0.10:
        return "ABSENT"
    return "UNKNOWN"


def main():
    fixtures = json.loads((ROOT / "fixtures.json").read_text())["fixtures"]
    template = next(x["pixels"] for x in fixtures if x["id"] == "clear_connected")
    rows = []
    for item in fixtures:
        pixels = item["pixels"]
        band = [connected(pixels, t) for t in THRESHOLDS]
        count = sum(band)
        persistent = "PRESENT" if count >= 3 else "ABSENT" if count <= 1 else "UNKNOWN"
        rows.append({
            "case_id": item["id"],
            "pixel": label_pixel_template(pixels, template),
            "single": "PRESENT" if connected(pixels, 128) else "ABSENT",
            "persistent": persistent,
            "connected_threshold_count": count,
            "application_effect": "UNKNOWN",
            "semantic_oracle_used": False,
            "pixel_visits": 81 * (1 + 1 + len(THRESHOLDS)),
        })
    out = {"schema": "topology-6183-candidate-v1", "rows": rows}
    (OUT_DIR / "candidate.raw.json").write_text(json.dumps(out, sort_keys=True, indent=2) + "\n")


if __name__ == "__main__":
    main()
