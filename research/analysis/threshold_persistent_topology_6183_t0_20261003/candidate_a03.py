#!/usr/bin/env python3
"""Image-only route connectivity and outline-hole classifier for #6183 A03."""
import json
import os
from collections import deque
from pathlib import Path

ROOT = Path(__file__).parent
OUT = Path(os.environ.get("OUT_DIR", ROOT))


def decode(case, palette, scale):
    rows = [[palette[ch] for ch in row for _ in range(scale)] for row in case["rows"] for _ in range(scale)]
    endpoints = [[x * scale, y * scale] for x, y in case["endpoints"]]
    return rows, endpoints


def route_connected(image, endpoints, threshold):
    h, w = len(image), len(image[0])
    start, goal = map(tuple, endpoints)
    if image[start[1]][start[0]] <= threshold:
        return False
    todo, seen = deque([start]), {start}
    while todo:
        x, y = todo.popleft()
        if (x, y) == goal:
            return True
        for nx, ny in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)):
            if 0 <= nx < w and 0 <= ny < h and (nx,ny) not in seen and image[ny][nx] > threshold:
                seen.add((nx,ny)); todo.append((nx,ny))
    return False


def hole_count(image, threshold):
    h, w = len(image), len(image[0])
    background = {(x,y) for y in range(h) for x in range(w) if image[y][x] <= threshold}
    outside = {p for p in background if p[0] in (0,w-1) or p[1] in (0,h-1)}
    todo = deque(outside)
    while todo:
        x,y = todo.popleft()
        for q in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)):
            if q in background and q not in outside:
                outside.add(q); todo.append(q)
    unseen = background - outside
    holes = 0
    while unseen:
        holes += 1
        seed = unseen.pop(); todo = deque([seed])
        while todo:
            x,y = todo.popleft()
            for q in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)):
                if q in unseen:
                    unseen.remove(q); todo.append(q)
    return holes


def predicate(image, endpoints, kind, threshold):
    return route_connected(image, endpoints, threshold) if kind == "route" else hole_count(image, threshold) == 1


def classify(votes):
    n = sum(votes)
    return "PRESENT" if n >= 3 else "ABSENT" if n <= 1 else "UNKNOWN"


def main():
    data = json.loads((ROOT / "fixtures_a03.json").read_text())
    cases, palette, thresholds = data["cases"], data["palette"], data["thresholds"]
    refs = {c["id"]: c for c in cases}
    rows = []
    for case in cases:
        for scale in data["scales"]:
            image, endpoints = decode(case, palette, scale)
            reference, _ = decode(refs[case["reference"]], palette, scale)
            pixels = [v for row in image for v in row]
            refpixels = [v for row in reference for v in row]
            delta = sum(abs(a-b) for a,b in zip(pixels, refpixels)) / (255 * len(pixels))
            pixel = "PRESENT" if delta <= .02 else "ABSENT" if delta >= .10 else "UNKNOWN"
            single = "PRESENT" if predicate(image, endpoints, case["predicate"], 128) else "ABSENT"
            votes = [predicate(image, endpoints, case["predicate"], t) for t in thresholds]
            rows.append({
                "case_id": f"{case['id']}@{scale}x", "base_id": case["id"], "scale": scale,
                "pixel": pixel, "single": single, "persistent": classify(votes),
                "threshold_matches": sum(votes), "application_effect": "UNKNOWN",
                "semantic_oracle_used": False, "pixel_visits": len(pixels) * (2 + len(thresholds))
            })
    (OUT / "candidate.raw.json").write_text(json.dumps({"schema":"topology-6183-a03-candidate-v1","rows":rows}, sort_keys=True, indent=2) + "\n")


if __name__ == "__main__":
    main()
