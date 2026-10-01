#!/usr/bin/env python3
"""Deterministic local synthetic form renderer and geometry-label audit."""
import hashlib
import json
import os
from pathlib import Path

from PIL import Image, ImageDraw

WIDTH, HEIGHT = 1280, 800
CELL = 32
SPLIT = {f"family-{i:02d}": ("train" if i <= 8 else "held_out")
         for i in range(1, 13)}
PALETTES = [((246, 248, 252), (33, 76, 130), (38, 110, 82)),
            ((250, 246, 239), (126, 67, 42), (38, 101, 145)),
            ((244, 250, 246), (43, 92, 64), (138, 67, 49)),
            ((249, 245, 251), (97, 56, 125), (32, 105, 101))]


def digest(data):
    return hashlib.sha256(data).hexdigest()


def specs():
    result = []
    for family in range(1, 13):
        # Family-specific form geometry; the fixed variants change harmless
        # content and theme but preserve exact renderer-derived target centers.
        left = 96 + ((family * 37) % 7) * 32
        top = 112 + ((family * 29) % 5) * 32
        form_w = 672 + ((family * 53) % 5) * 32
        field_x = left + 176 + ((family * 11) % 4) * 32
        field_y = top + 224 + ((family * 17) % 3) * 32
        submit_x = left + form_w - 112
        submit_y = top + 480 + ((family * 13) % 3) * 32
        result.append({"family_id": f"family-{family:02d}", "split": SPLIT[f"family-{family:02d}"],
                       "geometry": {"left": left, "top": top, "width": form_w,
                                    "field": [field_x, field_y], "submit": [submit_x, submit_y]}})
    return result


def render(spec, variant):
    g = spec["geometry"]
    bg, primary, button = PALETTES[(int(spec["family_id"][-2:]) + variant) % len(PALETTES)]
    image = Image.new("RGB", (WIDTH, HEIGHT), bg)
    d = ImageDraw.Draw(image)
    d.rectangle((0, 0, WIDTH, 64), fill=primary)
    d.rectangle((g["left"], g["top"], g["left"] + g["width"], g["top"] + 544),
                fill=(255, 255, 255), outline=(182, 190, 202), width=2)
    # Fixed-width neutral labels create a synthetic form appearance without
    # introducing a font dependency into coordinates or image variation.
    d.rectangle((g["left"] + 48, g["top"] + 64, g["left"] + 272, g["top"] + 80), fill=primary)
    d.rectangle((g["field"][0] - 144, g["field"][1] - 16,
                 g["field"][0] + 144, g["field"][1] + 48),
                fill=(255, 255, 255), outline=(105, 117, 132), width=2)
    d.rectangle((g["submit"][0] - 80, g["submit"][1] - 24,
                 g["submit"][0] + 80, g["submit"][1] + 24), fill=button)
    # Variant-specific decorative marker is remote from target regions.
    marker_x = 1000 + variant * 24
    d.rectangle((marker_x, 96, marker_x + 12, 108), fill=(25 + variant * 12, 25, 25))
    return image


def point_contract(point):
    return {"point_space": "source_observation_pixels",
            "point": {"x": int(point[0]), "y": int(point[1])},
            "motion_model": "surface_origin_translation"}


def candidate(g):
    return {"format": "compiled-form-grounding-v1",
            "field": point_contract(g["field"]), "submit": point_contract(g["submit"]),
            "method": {"first_action": "enter_exact_token",
                       "continue_when": "field_pixels_changed_and_submit_revalidated",
                       "second_action": "activate_submit",
                       "complete_when": "submission_pixels_changed_then_independent_score"}}


def main():
    here = Path(__file__).resolve().parent
    out = Path(os.environ.get("RESULT_ROOT", str(here / "out"))).resolve()
    out.mkdir(parents=True, exist_ok=True)
    specs_value = specs()
    records = []
    for spec in specs_value:
        fam = spec["family_id"]
        for variant in range(4):
            image = render(spec, variant)
            raw = image.tobytes()
            file_raw = b""
            from io import BytesIO
            stream = BytesIO()
            image.save(stream, format="PNG", optimize=False, compress_level=9)
            file_raw = stream.getvalue()
            path = out / f"{fam}-v{variant}.png"
            path.write_bytes(file_raw)
            records.append({"family_id": fam, "split": spec["split"], "variant": variant,
                            "geometry": spec["geometry"], "rgb_sha256": digest(raw),
                            "png_sha256": digest(file_raw), "candidate": candidate(spec["geometry"])})
    manifest = {"format": "gpu-grounding-template-diversity-cpu-gate-v1",
                "size": [WIDTH, HEIGHT], "cell": CELL, "families": specs_value,
                "records": records}
    payload = (json.dumps(manifest, sort_keys=True, indent=2) + "\n").encode()
    (out / "manifest.json").write_bytes(payload)
    print(json.dumps({"families": len(specs_value), "images": len(records),
                      "manifest_sha256": digest(payload), "output": str(out)}, sort_keys=True))


if __name__ == "__main__":
    main()
