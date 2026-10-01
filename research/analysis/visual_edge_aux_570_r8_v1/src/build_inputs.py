#!/usr/bin/env python3
"""Build fixed synthetic dense-control screenshots for Issue #4885."""
from __future__ import annotations

import hashlib
import json
import os
import random
from pathlib import Path

import PIL
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

W, H = 1280, 800
FONT = Path(os.environ.get("FONT_PATH", r"C:\Windows\Fonts\arial.ttf"))
PROMPT = (
    "You are inspecting a settings dashboard. You may receive one or two images. "
    "Image 1 is the authoritative source screenshot. If image 2 is present, it is "
    "a pixel-aligned grayscale edge view derived from image 1; use it only as "
    "supplementary geometry. Find the Archive button inside the card whose exact "
    "title is {title}. If that exact card/button is absent, abstain. Return only "
    "JSON with present (boolean) and point ([integer x, integer y] at the button "
    "center in image-1 coordinates, or null when absent). Do not click anything."
)

FORMAL = [(f"F{i:02d}", 5708820 + i, i <= 10) for i in range(1, 13)]
CONSTRUCTION = [(f"C{i:02d}", 5708810 + i, True) for i in range(1, 3)]


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def draw_screen(seed: int, present: bool) -> tuple[Image.Image, dict]:
    rng = random.Random(seed)
    font10 = ImageFont.truetype(str(FONT), 10)
    font11 = ImageFont.truetype(str(FONT), 11)
    font13 = ImageFont.truetype(str(FONT), 13)
    im = Image.new("RGB", (W, H), "#e8ebef")
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, W, 48), fill="#202b3a")
    d.text((20, 17), "WORKSPACE   /   POLICY CONSOLE", fill="#f5f7fa", font=font13)
    d.rectangle((0, 48, 126, H), fill="#26364a")
    for j, label in enumerate(("Overview", "Policies", "Members", "History", "Settings")):
        d.text((16, 82 + j * 38), label, fill="#d7dee8", font=font11)
    d.text((152, 70), "Retention rules", fill="#182433", font=font13)
    d.text((152, 91), "12 matching policy cards  ·  updated just now", fill="#667386", font=font10)

    titles = [f"Retention {i:02d} / {rng.choice(['Alpha','Beta','Delta','North'])}" for i in range(1, 13)]
    target_index = rng.randrange(12)
    target_title = titles[target_index] if present else f"Retention {13 + (seed % 70):02d} / Missing"
    target_box = None
    card_w, card_h = 268, 211
    start_x, start_y, gx, gy = 151, 117, 10, 12
    for i, title in enumerate(titles):
        row, col = divmod(i, 4)
        x = start_x + col * (card_w + gx)
        y = start_y + row * (card_h + gy)
        d.rounded_rectangle((x, y, x + card_w, y + card_h), radius=4, fill="#ffffff", outline="#c4ccd6", width=1)
        d.text((x + 10, y + 10), title, fill="#26364a", font=font10)
        d.line((x + 10, y + 31, x + card_w - 10, y + 31), fill="#e5e9ee", width=1)
        # Dense small rows and repeated labels keep semantic identity in text;
        # the treatment contributes only a deterministic edge view.
        for k in range(5):
            yy = y + 43 + k * 18
            d.text((x + 10, yy), f"scope {rng.randrange(10, 99):02d}   expires {rng.choice(['30d','60d','90d'])}", fill="#596779", font=font10)
        d.rounded_rectangle((x + 166, y + 164, x + 250, y + 193), radius=3, fill="#f5f7fa", outline="#8e9aaa", width=1)
        d.text((x + 185, y + 173), "Archive", fill="#344256", font=font10)
        if present and i == target_index:
            target_box = [x + 166, y + 164, x + 250, y + 193]
    return im, {"target_title": target_title, "target_box": target_box, "target_index": target_index if present else None}


def main(out: str) -> None:
    outp = Path(out)
    outp.mkdir(parents=True, exist_ok=True)
    if any(outp.iterdir()):
        raise SystemExit("STOP_OUTPUT_NOT_EMPTY")
    rows = []
    for split, cases in (("construction", CONSTRUCTION), ("formal", FORMAL)):
        for case_id, seed, present in cases:
            raw, truth = draw_screen(seed, present)
            edge = ImageOps.autocontrast(ImageOps.grayscale(raw).filter(ImageFilter.FIND_EDGES)).convert("RGB")
            raw_bytes_path = outp / f"{case_id}.source.png"
            edge_bytes_path = outp / f"{case_id}.edge.png"
            raw.save(raw_bytes_path, format="PNG", optimize=False)
            edge.save(edge_bytes_path, format="PNG", optimize=False)
            rows.append({
                "case_id": case_id, "split": split, "seed": seed,
                "source_file": raw_bytes_path.name, "source_sha256": sha(raw_bytes_path.read_bytes()),
                "edge_file": edge_bytes_path.name, "edge_sha256": sha(edge_bytes_path.read_bytes()),
                "width": W, "height": H, "present": present, **truth,
                "prompt": PROMPT.format(title=truth["target_title"]),
            })
    manifest = {"format": "visual-edge-aux-570-r8-inputs-v1", "font_sha256": sha(FONT.read_bytes()), "pillow": PIL.__version__, "rows": rows}
    (outp / "manifest.json").write_text(json.dumps(manifest, sort_keys=True, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("output")
    main(ap.parse_args().output)
