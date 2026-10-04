#!/usr/bin/env python3
"""Prepare the four frozen grayscale crops using the G21 ROI/scale rule."""
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parent
ROWS = [
    ("calc-compiled-ocrlive-4d74-1.png", "repair-01.png", 127, 161),
    ("calc-compiled-digits-4d74-1.png", "repair-02.png", 127, 161),
    ("calc-compiled-digitunavailable-4d74-1.png", "repair-03.png", 127, 161),
    ("calc-measured-boundedread-4d74-1.png", "repair-04.png", 217, 161),
]

for source_name, output_name, x, y in ROWS:
    source = ROOT / "source" / source_name
    output = ROOT / "input" / output_name
    if output.exists():
        raise SystemExit(f"refusing to overwrite frozen input: {output_name}")
    subprocess.run(
        ["magick", str(source), "-crop", f"88x14+{x}+{y}", "+repage",
         "-colorspace", "Gray", "-filter", "Point", "-resize", "400%",
         "-bordercolor", "white", "-border", "20", str(output)],
        check=True,
    )
print("prepared 4 crops")
