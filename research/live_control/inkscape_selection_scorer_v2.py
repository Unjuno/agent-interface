"""Overlay-tolerant target identity plus visible Inkscape selection scoring."""
import hashlib
from pathlib import Path

from PIL import Image


SCHEMA = "inkscape-visible-selection-score-v2"


def _sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _red_support(image, roi):
    points = []
    for y in range(roi[1], roi[3]):
        for x in range(roi[0], roi[2]):
            red, green, blue = image.getpixel((x, y))
            if red >= 240 and green <= 20 and blue <= 20: points.append((x, y))
    if not points: return None
    xs, ys = [point[0] for point in points], [point[1] for point in points]
    return {"bbox": [min(xs), min(ys), max(xs) + 1, max(ys) + 1],
            "red_pixels": len(points)}


def _dark(image, box):
    return sum(1 for y in range(box[1], box[3]) for x in range(box[0], box[2])
               if max(image.getpixel((x, y))) <= 50)


def score(plan, image_path, *, edge_tolerance=1, coverage_minimum=0.8,
          expansion=18, per_side_minimum=10):
    if (type(plan) is not dict or plan.get("schema") != "inkscape-red-target-plan-v1" or
            plan.get("grants_input_authority") is not False):
        raise ValueError("exact no-authority source plan required")
    path = Path(image_path)
    with Image.open(path) as source:
        image = source.convert("RGB"); support = _red_support(image, plan["roi"])
        expected = plan["target"]; expected_box = expected["bbox"]
        edge_delta = None if support is None else [support["bbox"][index] - expected_box[index]
                                                    for index in range(4)]
        coverage = 0 if support is None else support["red_pixels"] / expected["red_pixels"]
        identity = (support is not None and
            all(abs(value) <= edge_tolerance for value in edge_delta) and
            coverage_minimum <= coverage <= 1.05)
        left, top, right, bottom = expected_box
        zones = {"left": [left-expansion, top-expansion, left, bottom+expansion],
                 "right": [right, top-expansion, right+expansion, bottom+expansion],
                 "top": [left, top-expansion, right, top],
                 "bottom": [left, bottom, right, bottom+expansion]}
        counts = {name: _dark(image, box) for name, box in zones.items()}
    handles = all(value >= per_side_minimum for value in counts.values())
    success = identity and handles
    return {"schema": SCHEMA, "success": success,
        "reason": ("target_identity_and_selection_handles_visible" if success else
                   "target_identity_changed" if not identity else
                   "selection_handles_missing"),
        "source_image_sha256": plan["source_image_sha256"],
        "scored_image_sha256": _sha(path), "expected_target": expected,
        "observed_support": support, "edge_delta": edge_delta,
        "red_coverage_ratio": coverage, "edge_tolerance": edge_tolerance,
        "coverage_minimum": coverage_minimum, "zones": zones,
        "dark_pixels": counts, "per_side_minimum": per_side_minimum,
        "target_identity_valid": identity, "selection_handles_visible": handles,
        "grants_input_authority": False}
