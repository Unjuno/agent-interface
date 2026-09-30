#!/usr/bin/env python3
"""Independent raw-image-only scorer; deliberately does not import refine.py."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

from PIL import Image

COLOR = (249, 115, 22)
TOL = 8
AREA_MIN, AREA_MAX = 1600, 12000
FILL_MIN, ASPECT_MIN, ASPECT_MAX = 0.86, 0.84, 1.19
EXPECTED_IDS = [f"case-{n:02d}-{'retained-arena' if n == 1 else 'positive' if n <= 6 else 'absent' if n == 7 else 'orange-circle-only' if n == 8 else 'orange-diamond-only' if n == 9 else 'ambiguous-multiple'}" for n in range(1, 13)]


def overlap(a: list[int], b: list[int]) -> float:
    x = max(0, min(a[2], b[2]) - max(a[0], b[0]))
    y = max(0, min(a[3], b[3]) - max(a[1], b[1]))
    inter = x * y
    union = (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - inter
    return inter / union if union else 0.0


def independent_boxes(path: Path) -> list[list[int]]:
    image = Image.open(path).convert("RGB")
    w, h = image.size
    pixels = image.load()
    visited = bytearray(w * h)
    boxes = []
    for y in range(h):
        for x in range(w):
            start = y * w + x
            p = pixels[x, y]
            if visited[start] or any(abs(p[k] - COLOR[k]) > TOL for k in range(3)):
                continue
            stack = [(x, y)]
            visited[start] = 1
            xs, ys = [], []
            while stack:
                cx, cy = stack.pop()
                xs.append(cx)
                ys.append(cy)
                for nx, ny in ((cx - 1, cy), (cx + 1, cy), (cx, cy - 1), (cx, cy + 1)):
                    if 0 <= nx < w and 0 <= ny < h:
                        ni = ny * w + nx
                        np = pixels[nx, ny]
                        if not visited[ni] and all(abs(np[k] - COLOR[k]) <= TOL for k in range(3)):
                            visited[ni] = 1
                            stack.append((nx, ny))
            x0, x1, y0, y1 = min(xs), max(xs) + 1, min(ys), max(ys) + 1
            bw, bh, count = x1 - x0, y1 - y0, len(xs)
            if AREA_MIN <= count <= AREA_MAX and ASPECT_MIN <= bw / bh <= ASPECT_MAX and count / (bw * bh) >= FILL_MIN:
                boxes.append([x0, y0, x1, y1])
    return sorted(boxes)


def audit(root: Path, prediction_path: Path) -> dict:
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    predictions = json.loads(prediction_path.read_text(encoding="utf-8"))
    errors: list[str] = []
    expected_rows = manifest.get("rows", [])
    actual = predictions.get("rows", [])
    if [r.get("id") for r in actual] != EXPECTED_IDS:
        errors.append("row_identity_or_denominator_mismatch")
    if len(expected_rows) != 12 or [r.get("id") for r in expected_rows] != EXPECTED_IDS:
        errors.append("manifest_identity_or_denominator_mismatch")
    matched = {r.get("id"): r for r in actual if isinstance(r, dict)}
    hit_ids, control_ids, rescued_ids = [], [], []
    ious = {}
    for item in expected_rows:
        rid = item["id"]
        frame = root / "panels" / f"{rid}.png"
        digest = hashlib.sha256(frame.read_bytes()).hexdigest()
        if digest != item.get("sha256"):
            errors.append(f"input_hash_mismatch:{rid}")
        found = independent_boxes(frame)
        prediction = matched.get(rid)
        if prediction is None:
            errors.append(f"prediction_missing:{rid}")
            continue
        reported = prediction.get("box_xyxy") if prediction.get("status") == "PROPOSAL" else None
        if item.get("kind", "").startswith("positive"):
            truth = item.get("expected_box_xyxy")
            best = max((overlap(truth, box) for box in found), default=0.0)
            score = overlap(truth, reported) if isinstance(reported, list) else 0.0
            ious[rid] = score
            if best < 0.95 or score < 0.95:
                errors.append(f"positive_localization_miss:{rid}")
            else:
                hit_ids.append(rid)
            if rid == "case-01-retained-arena" and prediction.get("source_point_xy") in ([830, 640], [920, 640]):
                px, py = prediction["source_point_xy"]
                if px < truth[0] or px >= truth[2] or py < truth[1] or py >= truth[3]:
                    rescued_ids.append(rid)
        else:
            if found:
                errors.append(f"control_input_unexpected_unique_square:{rid}")
            if reported is not None:
                errors.append(f"control_not_abstained:{rid}")
            else:
                control_ids.append(rid)
    if len(hit_ids) != 6:
        errors.append("positive_gate_not_6_of_6")
    if len(control_ids) != 6:
        errors.append("negative_ambiguous_gate_not_6_of_6")
    result = {"outcome": "PASS_SCOPED_LOCAL_REFINEMENT" if not errors else "FAIL_OR_HOLD", "positive_hits": hit_ids, "control_abstentions": control_ids, "out_of_bounds_coordinate_rescues": rescued_ids, "ious": ious, "errors": errors}
    return result


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("usage: audit.py dataset-dir predictions.json")
    result = audit(Path(sys.argv[1]), Path(sys.argv[2]))
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result["outcome"] == "PASS_SCOPED_LOCAL_REFINEMENT" else 1)


if __name__ == "__main__":
    main()
