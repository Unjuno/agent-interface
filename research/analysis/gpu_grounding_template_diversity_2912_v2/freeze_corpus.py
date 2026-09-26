"""Create/check the exact pre-formal 48-image Pillow raster manifest."""
from __future__ import annotations

import argparse
import hashlib
import io
import json
from pathlib import Path

import PIL

from render import FAMILIES, RENDERER_ID, RESIZED, render, source_family_sha256


EXPECTED_PILLOW = "10.2.0"


def make_manifest():
    if PIL.__version__ != EXPECTED_PILLOW:
        raise RuntimeError(f"frozen renderer requires Pillow {EXPECTED_PILLOW}, got {PIL.__version__}")
    rows = []
    for spec in FAMILIES:
        for variant in range(4):
            image, label = render(spec, variant)
            encoded = io.BytesIO()
            image.save(encoded, format="PNG", optimize=False, compress_level=9)
            rows.append({**label,
                         "image_id": f"{spec['id']}/variant-{variant}",
                         "pixel_sha256": hashlib.sha256(image.tobytes()).hexdigest(),
                         "png_sha256": hashlib.sha256(encoded.getvalue()).hexdigest()})
    return {"schema": "issue4561-rendered-corpus-manifest-v1",
            "renderer_id": RENDERER_ID, "pillow": PIL.__version__,
            "canvas": [1280, 800], "resized": list(RESIZED),
            "train_families": [f["id"] for f in FAMILIES[:8]],
            "narrow_families": [f["id"] for f in FAMILIES[:2]],
            "heldout_families": [f["id"] for f in FAMILIES[8:]],
            "families": [{"family_id": f["id"], "family_sha256": source_family_sha256(f)}
                         for f in FAMILIES],
            "images": rows}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path(__file__).with_name("corpus_manifest.json"))
    args = parser.parse_args()
    payload = json.dumps(make_manifest(), sort_keys=True, indent=2) + "\n"
    args.output.write_text(payload, encoding="utf-8")
    print(hashlib.sha256(payload.encode("utf-8")).hexdigest())


if __name__ == "__main__":
    main()
