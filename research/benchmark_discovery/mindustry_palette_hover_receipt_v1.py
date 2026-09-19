"""Verify one click-free persistent Mindustry palette hover receipt."""
import hashlib
from pathlib import Path

from PIL import Image, ImageChops


def crop_digest(path, box):
    with Image.open(path) as opened:
        crop = opened.convert("RGB").crop(tuple(box))
    return crop, hashlib.sha256(crop.tobytes()).hexdigest()


def verify(records, steps, point, tooltip_box, runtime_dir, source_image):
    expected = [{"op": "pointer_move", "x": point[0], "y": point[1]},
                {"op": "settle", "quiet_ms": 100, "timeout_ms": 1200},
                {"op": "observe"}]
    if steps != expected:
        raise ValueError("Mindustry hover program mismatch")
    admissions = [row for row in records if row.get("event") == "pointer_admission"]
    if [(row.get("step"), row.get("operation"), row.get("payload"))
            for row in admissions] != [(0, "move", {"x": point[0], "y": point[1]})]:
        raise ValueError("hover receipt must contain one bound move and no button input")
    settles = [row for row in records if row.get("event") == "settle_result"]
    if len(settles) != 1 or settles[0].get("reason") != "pixel_quiet":
        raise ValueError("pixel-quiet hover settle required")
    dwell = [row for row in records if row.get("event") == "observation"
             and row.get("step") == 1]
    persistent = [row for row in records if row.get("event") == "observation"
                  and row.get("step") == 2]
    if len(dwell) < 2 or len(persistent) != 1:
        raise ValueError("settled and persistent hover observations required")
    first, second = dwell[-1], persistent[0]
    if first.get("pointer_binding") != second.get("pointer_binding"):
        raise ValueError("hover binding changed")
    if first.get("focus_samples_match") is not True or second.get("focus_samples_match") is not True:
        raise ValueError("focus changed during hover receipt")
    runtime_dir = Path(runtime_dir)
    first_crop, first_digest = crop_digest(runtime_dir / Path(first["image"]).name, tooltip_box)
    second_crop, second_digest = crop_digest(runtime_dir / Path(second["image"]).name, tooltip_box)
    if first_digest != second_digest:
        raise ValueError("Mindustry tooltip panel did not persist exactly")
    source_crop, _ = crop_digest(source_image, tooltip_box)
    changed = sum(1 for value in ImageChops.difference(source_crop, second_crop).getdata()
                  if value != (0, 0, 0))
    if changed < 500:
        raise ValueError("hover did not produce enough tooltip-panel evidence")
    receipt = {"receipt_index": 1, "point": point,
               "dwell_sequence": first["sequence"],
               "persistent_sequence": second["sequence"],
               "tooltip": {"box": tooltip_box, "size": list(second_crop.size),
                           "changed_pixels_from_source": changed,
                           "pixels_sha256": second_digest},
               "authority": "observation evidence only; grants no input authority"}
    return {"status": "READY", "binding": first["pointer_binding"],
            "receipts": [receipt], "authority":
            "composed observation evidence only; grants no input authority"}
