#!/usr/bin/env python3
"""Independent integrity checks for the CPU renderer construction gate."""
import hashlib
import json
from pathlib import Path

from PIL import Image

from render_audit import CELL, HEIGHT, WIDTH, candidate, digest, render, specs


def validate(value):
    if type(value) is not dict or set(value) != {"format", "field", "submit", "method"}:
        raise ValueError("exact compiled form grounding required")
    if value["format"] != "compiled-form-grounding-v1":
        raise ValueError("compiled form grounding v1 required")
    points = []
    for key in ("field", "submit"):
        target = value[key]
        if type(target) is not dict or set(target) != {"point_space", "point", "motion_model"}:
            raise ValueError("exact target contract required")
        if target["point_space"] != "source_observation_pixels" or target["motion_model"] != "surface_origin_translation":
            raise ValueError("point semantics mismatch")
        point = target["point"]
        if type(point) is not dict or set(point) != {"x", "y"}:
            raise ValueError("point mapping mismatch")
        x, y = point["x"], point["y"]
        if type(x) is not int or type(y) is not int or not (0 <= x < WIDTH and 0 <= y < HEIGHT):
            raise ValueError("point outside source observation")
        points.append((x, y))
    if points[0] == points[1]:
        raise ValueError("field and submit points must differ")
    expected = {"first_action": "enter_exact_token",
                "continue_when": "field_pixels_changed_and_submit_revalidated",
                "second_action": "activate_submit",
                "complete_when": "submission_pixels_changed_then_independent_score"}
    if value["method"] != expected:
        raise ValueError("method contract mismatch")
    return points


def audit(out):
    manifest_bytes = (out / "manifest.json").read_bytes()
    manifest = json.loads(manifest_bytes)
    if manifest["format"] != "gpu-grounding-template-diversity-cpu-gate-v1":
        raise ValueError("manifest format mismatch")
    family_specs = specs()
    by_family = {x["family_id"]: x for x in family_specs}
    if len(by_family) != 12 or len(manifest["records"]) != 48:
        raise ValueError("family/image count mismatch")
    if set(x["family_id"] for x in manifest["families"]) != set(by_family):
        raise ValueError("family specification set mismatch")
    train = {x["family_id"] for x in manifest["families"] if x["split"] == "train"}
    held = {x["family_id"] for x in manifest["families"] if x["split"] == "held_out"}
    if train & held or len(train) != 8 or len(held) != 4:
        raise ValueError("family-level split leakage")
    seen_rgb = set()
    for row in manifest["records"]:
        fam, variant = row["family_id"], row["variant"]
        spec = by_family[fam]
        expected_image = render(spec, variant)
        if expected_image.tobytes() and digest(expected_image.tobytes()) != row["rgb_sha256"]:
            raise ValueError("rendered RGB digest mismatch")
        if row["split"] != spec["split"] or row["geometry"] != spec["geometry"]:
            raise ValueError("split or geometry does not match source specification")
        png_path = out / f"{fam}-v{variant}.png"
        png = png_path.read_bytes()
        if digest(png) != row["png_sha256"]:
            raise ValueError("PNG digest mismatch")
        with Image.open(png_path) as im:
            actual = im.convert("RGB").tobytes()
        if actual != expected_image.tobytes():
            raise ValueError("PNG pixels differ from renderer")
        if row["rgb_sha256"] in seen_rgb:
            raise ValueError("duplicate RGB source")
        seen_rgb.add(row["rgb_sha256"])
        points = validate(row["candidate"])
        if tuple(points) != (tuple(spec["geometry"]["field"]), tuple(spec["geometry"]["submit"])):
            raise ValueError("strict validator accepted wrong geometry label")
        for x, y in points:
            if x % CELL != CELL // 2 or y % CELL != CELL // 2:
                raise ValueError("coordinate is not centered in a 32px cell")
    return {"status": "PASS_CPU_RENDERER_COORDINATE_GATE", "families": 12,
            "train_families": 8, "held_out_families": 4, "images": 48,
            "unique_rgb_hashes": len(seen_rgb), "manifest_sha256": digest(manifest_bytes)}


def main():
    import sys
    out = Path(sys.argv[1]).resolve()
    print(json.dumps(audit(out), sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
