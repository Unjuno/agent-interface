"""Fixture-scoped visual planner and fresh target validator for Inkscape."""
import hashlib
from pathlib import Path

from PIL import Image


SCHEMA = "inkscape-red-target-plan-v1"


def _sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _target(path, roi):
    if (type(roi) is not list or len(roi) != 4 or
            any(type(value) is not int for value in roi)):
        raise ValueError("integer ROI required")
    with Image.open(path) as source:
        image = source.convert("RGB")
        left, top, right, bottom = roi
        if not (0 <= left < right <= image.width and 0 <= top < bottom <= image.height):
            raise ValueError("ROI outside image")
        pixels = image.load(); points = []
        for y in range(top, bottom):
            for x in range(left, right):
                red, green, blue = pixels[x, y]
                if red >= 240 and green <= 20 and blue <= 20:
                    points.append((x, y))
    if len(points) < 100:
        raise ValueError("red target missing")
    xs, ys = [p[0] for p in points], [p[1] for p in points]
    box = [min(xs), min(ys), max(xs) + 1, max(ys) + 1]
    area = (box[2] - box[0]) * (box[3] - box[1])
    if area != len(points):
        raise ValueError("red target must be one solid rectangle")
    return {"bbox": box, "red_pixels": len(points),
            "center": [(box[0] + box[2] - 1) // 2,
                       (box[1] + box[3] - 1) // 2]}


def prepare(image_path, roi):
    target = _target(image_path, roi)
    return {"schema": SCHEMA, "source_image_sha256": _sha(image_path),
        "roi": list(roi), "target": target,
        "action": {"op": "pointer_click", "x": target["center"][0],
                   "y": target["center"][1], "duration_ms": 80},
        "grants_input_authority": False}


def validate(plan, fresh_image_path):
    if (type(plan) is not dict or plan.get("schema") != SCHEMA or
            plan.get("grants_input_authority") is not False):
        raise ValueError("exact no-authority plan required")
    current = _target(fresh_image_path, plan["roi"])
    same = current == plan["target"]
    return {"schema": "inkscape-red-target-validation-v1",
        "status": "VALID_CURRENT" if same else "REJECTED_TARGET_CHANGED",
        "source_image_sha256": plan["source_image_sha256"],
        "fresh_image_sha256": _sha(fresh_image_path),
        "source_target": plan["target"], "fresh_target": current,
        "action": plan["action"], "action_may_proceed_to_admission": same,
        "requires_new_decision": not same,
        "grants_input_authority": False}
