#!/usr/bin/env python3
"""Generate the frozen 12-panel held-out cohort; no candidate scoring occurs here."""
from __future__ import annotations
import json
import random
import sys
from pathlib import Path
from PIL import Image, ImageDraw

W, H = 720, 520
ORANGE = (249, 115, 22)
BG = (246, 248, 250)
DISTRACTORS = ((220, 55, 60), (35, 120, 220), (245, 205, 50))
SEED = 4695027


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: generate_heldout.py output-dir")
    out = Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True)
    rng = random.Random(SEED)
    specs = [
        ("heldout-01-positive-min-area", "positive-heldout", [(61, 77, 101, 117)]),
        ("heldout-02-positive-low", "positive-heldout", [(601, 83, 647, 129)]),
        ("heldout-03-positive-mid", "positive-heldout", [(274, 357, 342, 425)]),
        ("heldout-04-positive-max", "positive-heldout", [(482, 211, 590, 319)]),
        ("heldout-05-absent", "absent", []),
        ("heldout-06-circle", "absent-orange-nonsquare", []),
        ("heldout-07-diamond", "absent-orange-nonsquare", []),
        ("heldout-08-thin-rectangle", "absent-orange-nonsquare", []),
        ("heldout-09-ambiguous-two", "ambiguous-multiple-squares", [(101, 126, 149, 174), (541, 326, 605, 390)]),
        ("heldout-10-ambiguous-three", "ambiguous-multiple-squares", [(82, 360, 124, 402), (302, 95, 358, 151), (548, 204, 632, 288)]),
        ("heldout-11-ambiguous-four", "ambiguous-multiple-squares", [(59, 63, 101, 105), (221, 301, 269, 349), (429, 103, 485, 159), (612, 382, 672, 442)]),
        ("heldout-12-ambiguous-edge", "ambiguous-multiple-squares", [(0, 0, 52, 52), (668, 468, 720, 520)]),
    ]
    rows = []
    for name, kind, boxes in specs:
        im = Image.new("RGB", (W, H), BG); d = ImageDraw.Draw(im)
        # Stable, non-target distractors add spatial clutter without sharing the target hue.
        for _ in range(7):
            x, y = rng.randrange(20, W-20), rng.randrange(20, H-20)
            color = rng.choice(DISTRACTORS); radius = rng.randrange(5, 14)
            d.ellipse((x-radius, y-radius, x+radius, y+radius), fill=color)
        for box in boxes:
            d.rectangle((box[0], box[1], box[2]-1, box[3]-1), fill=ORANGE)
        if name == "heldout-06-circle":
            d.ellipse((322, 210, 402, 290), fill=ORANGE)
        elif name == "heldout-07-diamond":
            d.polygon([(360, 190), (420, 250), (360, 310), (300, 250)], fill=ORANGE)
        elif name == "heldout-08-thin-rectangle":
            d.rectangle((284, 232, 404, 263), fill=ORANGE)
        path=out/f"{name}.png"; im.save(path, format="PNG", optimize=False)
        rows.append({"id":name,"kind":kind,"file":path.name,"width":W,"height":H,"sha256":__import__("hashlib").sha256(path.read_bytes()).hexdigest(),"expected_box_xyxy":boxes[0] if kind=="positive-heldout" else None,"expected_eligible_components":len(boxes) if boxes else 0})
    (out/"manifest.json").write_text(json.dumps({"schema":"arena-v1-cv-grounding-v2-heldout-v1","seed":SEED,"rows":rows},indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"rows":len(rows),"positive":4,"controls":8},indent=2))

if __name__ == "__main__": main()
