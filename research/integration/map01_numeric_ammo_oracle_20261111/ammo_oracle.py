"""Narrow MAP01 pistol-ammo HUD classifier for the frozen GZDoom setup.

This is not general OCR. It compares a small fixed digit patch against retained
50 and 49 templates, allowing one global RGB channel permutation to account for
the palette transition seen in R96.
"""

from __future__ import annotations

import itertools
from pathlib import Path

from PIL import Image


PATCH_SIZE = (40, 30)
FRAME_SIZE = (1520, 825)
AMMO_DIGIT_BOX = (470, 778, 510, 808)
MAX_TEMPLATE_DISTANCE = 0.02
MIN_CLASS_MARGIN = 0.10


def _rgb_pixels(image: Image.Image) -> list[tuple[int, int, int]]:
    if image.size != PATCH_SIZE:
        raise ValueError(f"ammo patch must be {PATCH_SIZE}, got {image.size}")
    return list(image.convert("RGB").getdata())


def _load_pixels(path: Path) -> list[tuple[int, int, int]]:
    with Image.open(path) as image:
        return _rgb_pixels(image)


def _distance(sample: list[tuple[int, int, int]],
              reference: list[tuple[int, int, int]]) -> tuple[float, tuple[int, ...]]:
    candidates = []
    for permutation in itertools.permutations(range(3)):
        changed = sum(tuple(pixel[index] for index in permutation) != expected
                      for pixel, expected in zip(sample, reference))
        candidates.append((changed / len(sample), permutation))
    return min(candidates)


def classify_ammo(image_path: Path, template_dir: Path) -> dict:
    with Image.open(image_path) as image:
        return classify_ammo_image(image, template_dir)


def classify_ammo_image(image: Image.Image, template_dir: Path) -> dict:
    sample = _rgb_pixels(image)
    scores = {}
    for value in ("49", "50"):
        reference = _load_pixels(template_dir / f"ammo_{value}_template.png")
        scores[value], _ = _distance(sample, reference)
    ranked = sorted(scores.items(), key=lambda row: row[1])
    best, second = ranked
    margin = second[1] - best[1]
    if best[1] > MAX_TEMPLATE_DISTANCE or margin < MIN_CLASS_MARGIN:
        return {"status": "unknown", "scores": scores, "margin": margin}
    return {"status": "classified", "value": best[0], "scores": scores,
            "margin": margin, "scope": "frozen MAP01 assets and 1520x825 HUD geometry"}


def classify_ammo_frame(image: Image.Image, template_dir: Path) -> dict:
    if image.size != FRAME_SIZE:
        return {"status": "unknown", "reason": "frame_geometry_mismatch"}
    return classify_ammo_image(image.crop(AMMO_DIGIT_BOX), template_dir)


def verify_ammo_transition(before_path: Path, after_path: Path,
                           template_dir: Path, expected_before: str = "50",
                           expected_after: str = "49") -> dict:
    before = classify_ammo(before_path, template_dir)
    after = classify_ammo(after_path, template_dir)
    if before["status"] != "classified" or after["status"] != "classified":
        return {"status": "unknown", "before": before, "after": after}
    if before["value"] != expected_before:
        return {"status": "unknown", "reason": "baseline_value_mismatch",
                "before": before, "after": after}
    status = "success" if after["value"] == expected_after else "failure"
    return {"status": status, "before": before, "after": after,
            "expected_transition": [expected_before, expected_after]}
