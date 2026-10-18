#!/usr/bin/env python3
"""Recompute the frozen yellow/red counts on the opaque-labeled frame sample."""
import json
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SAMPLE = json.loads((HERE / "SAMPLE.json").read_text(encoding="utf-8"))
LABELS = {row["code"]: row for row in json.loads(
    (HERE / "BLIND_LABELS.json").read_text(encoding="utf-8"))["labels"]}
COMMIT = SAMPLE["commit"]
BASE = "research/doom/results/map01-v39-coast-liveness-live-01/runtime"


def count_masks(path):
    raw = subprocess.run(
        ["magick", str(path), "-crop", "380x270+450+250", "+repage",
         "-depth", "8", "RGB:-"], check=True, stdout=subprocess.PIPE).stdout
    if len(raw) != 380 * 270 * 3:
        raise ValueError(f"unexpected crop byte count for {path}: {len(raw)}")
    yellow = red = 0
    for i in range(0, len(raw), 3):
        r, g, b = raw[i:i + 3]
        yellow += r > 180 and g > 100 and b < 100 and r > 0.8 * g and g > 1.5 * b
        red += r > 70 and r > 1.25 * g and r > 1.25 * b
    return yellow, red


rows = []
for entry in SAMPLE["entries"]:
    rel = f"{BASE}/{entry['sequence']:03d}.png"
    path = ROOT / rel
    yellow, red = count_masks(path)
    rows.append({
        "code": entry["code"], "sequence": entry["sequence"],
        "enemy_visible": LABELS[entry["code"]]["enemy_visible"],
        "confidence": LABELS[entry["code"]]["confidence"],
        "yellow_count": yellow, "yellow_gt_200": yellow > 200,
        "red_count": red, "source_sha256": entry["sha256"],
    })
result = {
    "source_commit": COMMIT,
    "roi_xywh": [450, 250, 380, 270],
    "yellow_rule": "R>180,G>100,B<100,R>0.8G,G>1.5B,count>200",
    "red_rule": "R>70,R>1.25G,R>1.25B",
    "rows": sorted(rows, key=lambda row: row["code"]),
}
(HERE / "OUTPUT.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"status": "COUNTS_RECOMPUTED", "rows": len(rows)}, indent=2))
