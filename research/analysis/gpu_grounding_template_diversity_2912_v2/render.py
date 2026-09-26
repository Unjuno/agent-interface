"""Deterministic Pillow renderer for the Issue #4561 synthetic form corpus."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


RENDERER_ID = "issue4561-pillow-10.2.0-raster-v1"
CANVAS = (1280, 800)
RESIZED = (160, 100)
OUTPUT_GRID = (8, 10)

# Distinct source geometry families. Labels refer to whole pooled cells, then
# are converted to the center of the corresponding source-pixel footprint.
FAMILIES = (
    {"id": "family-01", "field": [2, 2], "submit": [2, 4], "card": [80, 72, 580, 344], "sidebar": True},
    {"id": "family-02", "field": [1, 3], "submit": [1, 6], "card": [184, 48, 700, 296], "sidebar": False},
    {"id": "family-03", "field": [3, 1], "submit": [4, 3], "card": [32, 176, 456, 528], "sidebar": True},
    {"id": "family-04", "field": [4, 5], "submit": [5, 8], "card": [416, 248, 944, 616], "sidebar": False},
    {"id": "family-05", "field": [2, 6], "submit": [3, 8], "card": [560, 104, 1104, 432], "sidebar": True},
    {"id": "family-06", "field": [5, 2], "submit": [6, 4], "card": [128, 352, 632, 728], "sidebar": False},
    {"id": "family-07", "field": [1, 7], "submit": [2, 9], "card": [752, 80, 1224, 392], "sidebar": True},
    {"id": "family-08", "field": [6, 6], "submit": [6, 9], "card": [616, 408, 1160, 768], "sidebar": False},
    {"id": "family-09", "field": [0, 1], "submit": [0, 3], "card": [16, 16, 440, 248], "sidebar": True},
    {"id": "family-10", "field": [3, 6], "submit": [4, 8], "card": [696, 192, 1248, 552], "sidebar": False},
    {"id": "family-11", "field": [5, 0], "submit": [6, 2], "card": [0, 360, 456, 792], "sidebar": True},
    {"id": "family-12", "field": [0, 6], "submit": [1, 8], "card": [680, 0, 1272, 304], "sidebar": False},
)

THEMES = (
    {"background": "#edf1f4", "card": "#ffffff", "ink": "#263746", "accent": "#247ba0", "field": "#fbfcfd"},
    {"background": "#f3eee6", "card": "#fffaf2", "ink": "#39312a", "accent": "#a04b32", "field": "#ffffff"},
    {"background": "#e9eef0", "card": "#f8fbfc", "ink": "#213b3f", "accent": "#517a62", "field": "#ffffff"},
    {"background": "#eeebf5", "card": "#fcfaff", "ink": "#332d45", "accent": "#7059a6", "field": "#ffffff"},
)


def pooled_cell_centers() -> list[list[list[int]]]:
    """Map 8x10 fixed adaptive-pool output cells to source-pixel centers."""
    def bounds(source: int, target: int, i: int) -> tuple[int, int]:
        start = (i * source) // target
        end = ((i + 1) * source + target - 1) // target
        return start, end

    rows = []
    for r in range(8):
        hs, he = bounds(25, 8, r)
        y = 16 * (hs + he)
        row = []
        for c in range(10):
            ws, we = bounds(40, 10, c)
            x = 16 * (ws + we)
            row.append([x, y])
        rows.append(row)
    return rows


CELL_CENTERS = pooled_cell_centers()


def canonical_json(value) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def source_family_sha256(spec: dict) -> str:
    return hashlib.sha256(canonical_json({"renderer": RENDERER_ID, "family": spec})).hexdigest()


def source_point(cell: list[int]) -> list[int]:
    r, c = cell
    if type(r) is not int or type(c) is not int or not (0 <= r < 8 and 0 <= c < 10):
        raise ValueError("invalid fixed-pool cell")
    return CELL_CENTERS[r][c].copy()


def render(spec: dict, variant: int) -> tuple[Image.Image, dict]:
    if not any(s["id"] == spec["id"] for s in FAMILIES):
        raise ValueError("unregistered source-template family")
    if type(variant) is not int or not 0 <= variant < 4:
        raise ValueError("variant must be in [0,3]")
    theme = THEMES[variant]
    im = Image.new("RGB", CANVAS, theme["background"])
    draw = ImageDraw.Draw(im)
    font = ImageFont.load_default()
    x0, y0, x1, y1 = spec["card"]
    draw.rounded_rectangle((x0, y0, x1, y1), radius=18 + 4 * variant, fill=theme["card"], outline="#b8c2ca", width=3)
    draw.text((x0 + 28, y0 + 20), ("Account access", "Profile details", "Workspace setup", "Contact preferences")[variant], fill=theme["ink"], font=font)

    # Decorative navigation and non-target fields vary between source families.
    if spec["sidebar"]:
        draw.rectangle((x0 + 20, y0 + 62, x0 + 136, min(y1 - 28, y0 + 264)), fill=theme["background"])
        for k in range(4):
            yy = y0 + 82 + k * 38
            if yy < y1 - 24:
                draw.rounded_rectangle((x0 + 34, yy, x0 + 118, yy + 10), radius=4, fill="#b7c1c9")
    # Non-target distractor control, intentionally distinct from exact labels.
    distract_x = min(x1 - 70, x0 + 210 + 17 * variant)
    distract_y = min(y1 - 42, y0 + 110 + 13 * variant)
    field_xy = source_point(spec["field"])
    submit_xy = source_point(spec["submit"])
    if max(abs(distract_x - field_xy[0]), abs(distract_y - field_xy[1])) > 100:
        draw.rectangle((distract_x - 38, distract_y - 16, distract_x + 38, distract_y + 16), outline="#87939b", width=2)
        draw.text((distract_x - 28, distract_y - 5), "Extra", fill="#65717a", font=font)

    # Draw actionable field/button around renderer-derived exact cell centers.
    fx, fy = field_xy
    draw.text((fx - 48, fy - 29), ("Email", "Name", "Code", "Search")[variant], fill=theme["ink"], font=font)
    draw.rounded_rectangle((fx - 50, fy - 14, fx + 50, fy + 14), radius=5, fill=theme["field"], outline=theme["accent"], width=3)
    sx, sy = submit_xy
    draw.rounded_rectangle((sx - 42, sy - 18, sx + 42, sy + 18), radius=8, fill=theme["accent"])
    draw.text((sx - 22, sy - 5), ("Continue", "Save", "Apply", "Send")[variant], fill="#ffffff", font=font)

    gray = im.convert("L").resize(RESIZED, Image.Resampling.BILINEAR)
    label = {"family_id": spec["id"], "family_sha256": source_family_sha256(spec),
             "variant": variant, "field_cell": spec["field"].copy(), "submit_cell": spec["submit"].copy(),
             "field_point": field_xy, "submit_point": submit_xy}
    return gray, label


def render_corpus(output: Path) -> list[dict]:
    output = Path(output)
    rows = []
    for spec in FAMILIES:
        for variant in range(4):
            image, label = render(spec, variant)
            path = output / spec["id"] / f"variant-{variant}.png"
            path.parent.mkdir(parents=True, exist_ok=True)
            image.save(path, format="PNG", optimize=False, compress_level=9)
            raw = path.read_bytes()
            rows.append({**label, "image": path.as_posix(), "image_sha256": hashlib.sha256(raw).hexdigest()})
    return rows
