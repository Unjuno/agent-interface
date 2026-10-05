"""Independent visible selection-handle scorer for the red Inkscape fixture."""
from pathlib import Path

from PIL import Image

try:
    from .inkscape_red_target_planner_v1 import validate
except ImportError:
    from inkscape_red_target_planner_v1 import validate


SCHEMA = "inkscape-visible-selection-score-v1"


def _dark(image, box):
    left, top, right, bottom = box
    return sum(1 for y in range(top, bottom) for x in range(left, right)
               if max(image.getpixel((x, y))) <= 50)


def score(plan, image_path, *, expansion=18, per_side_minimum=20):
    target_check = validate(plan, image_path)
    if target_check["status"] != "VALID_CURRENT":
        return {"schema": SCHEMA, "success": False,
            "reason": "target_changed", "target_validation": target_check,
            "grants_input_authority": False}
    with Image.open(Path(image_path)) as source:
        image = source.convert("RGB")
        left, top, right, bottom = target_check["fresh_target"]["bbox"]
        if not (left >= expansion and top >= expansion and
                right + expansion <= image.width and bottom + expansion <= image.height):
            raise ValueError("target lacks bounded selection-score margin")
        zones = {
            "left": [left - expansion, top - expansion, left, bottom + expansion],
            "right": [right, top - expansion, right + expansion, bottom + expansion],
            "top": [left, top - expansion, right, top],
            "bottom": [left, bottom, right, bottom + expansion],
        }
        counts = {name: _dark(image, box) for name, box in zones.items()}
    success = all(value >= per_side_minimum for value in counts.values())
    return {"schema": SCHEMA, "success": success,
        "reason": "four_sided_selection_handles_visible" if success else
                  "selection_handles_missing",
        "target_validation": target_check, "zones": zones,
        "dark_pixels": counts, "per_side_minimum": per_side_minimum,
        "grants_input_authority": False}
