#!/usr/bin/env python3
"""Build a fixed compact CV-grounding suite from the retained Arena frame."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw

W, H = 720, 520
BG = (16, 20, 27)
ORANGE = (249, 115, 22)


def square(draw: ImageDraw.ImageDraw, x: int, y: int, size: int, color=ORANGE) -> list[int]:
    draw.rectangle((x, y, x + size - 1, y + size - 1), fill=(255, 255, 255))
    draw.rectangle((x + 4, y + 4, x + size - 5, y + size - 5), fill=color)
    return [x + 4, y + 4, x + size - 4, y + size - 4]


def base() -> tuple[Image.Image, ImageDraw.ImageDraw]:
    image = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(image)
    d.rectangle((0, 0, W - 1, 108), fill=(17, 23, 31))
    d.line((0, 108, W, 108), fill=(70, 83, 99), width=2)
    return image, d


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("usage: generate_suite.py retained-frame.png output-dir")
    retained = Path(sys.argv[1])
    out = Path(sys.argv[2])
    out.mkdir(parents=True, exist_ok=True)
    panels = out / "panels"
    panels.mkdir(exist_ok=True)
    rows: list[dict] = []

    def save(name: str, image: Image.Image, kind: str, expected: list[int] | None) -> None:
        path = panels / f"{name}.png"
        image.save(path, format="PNG", optimize=False)
        raw = path.read_bytes()
        rows.append({"id": name, "kind": kind, "expected_box_xyxy": expected, "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()})

    original = Image.open(retained).convert("RGB")
    save("case-01-retained-arena", original, "positive-retained", [550, 418, 603, 471])

    # Five held-out-from-the-retained-frame positions/sizes; other colors stay distractors.
    positives = [(84, 198, 48), (580, 184, 52), (302, 410, 56), (130, 350, 64), (500, 300, 60)]
    for i, (x, y, size) in enumerate(positives, 2):
        image, d = base()
        d.rectangle((80, 180, 145, 245), fill=(239, 68, 68), outline=(255, 255, 255), width=3)
        d.rectangle((370, 220, 430, 270), fill=(234, 179, 8), outline=(255, 255, 255), width=3)
        d.ellipse((220, 310, 275, 365), fill=(249, 115, 22), outline=(255, 255, 255), width=3)
        box = square(d, x, y, size)
        save(f"case-{i:02d}-positive", image, "positive-synthetic", box)

    # Three absent-target controls: no orange square, though an orange circle/diamond may exist.
    image, d = base()
    d.rectangle((300, 260, 355, 315), fill=(239, 68, 68), outline=(255, 255, 255), width=3)
    d.rectangle((450, 330, 515, 380), fill=(234, 179, 8), outline=(255, 255, 255), width=3)
    save("case-07-absent", image, "absent", None)
    image, d = base()
    d.ellipse((320, 250, 379, 309), fill=ORANGE, outline=(255, 255, 255), width=3)
    d.rectangle((130, 300, 190, 355), fill=(239, 68, 68), outline=(255, 255, 255), width=3)
    save("case-08-orange-circle-only", image, "absent-orange-nonsquare", None)
    image, d = base()
    d.polygon([(350, 230), (390, 270), (350, 310), (310, 270)], fill=ORANGE, outline=(255, 255, 255))
    save("case-09-orange-diamond-only", image, "absent-orange-nonsquare", None)

    # Three ambiguous controls: multiple eligible orange squares must never be guessed.
    for i, boxes in enumerate(([(150, 250, 54), (470, 320, 54)], [(100, 190, 48), (335, 350, 64), (560, 210, 52)], [(240, 260, 56), (430, 260, 56)]), 10):
        image, d = base()
        d.rectangle((70, 175, 125, 230), fill=(239, 68, 68), outline=(255, 255, 255), width=3)
        for x, y, size in boxes:
            square(d, x, y, size)
        save(f"case-{i:02d}-ambiguous-multiple", image, "ambiguous-multiple-squares", None)

    manifest = {"schema": "arena-v1-cv-grounding-rescue-suite-v1", "width": W, "height": H, "orange_rgb": ORANGE, "retained_frame_sha256": hashlib.sha256(retained.read_bytes()).hexdigest(), "rows": rows}
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"rows": len(rows), "bytes": sum(x["bytes"] for x in rows), "manifest": manifest}, indent=2))


if __name__ == "__main__":
    main()
