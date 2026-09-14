"""Summarize a persistent visual drag effect without task or engine state."""
from pathlib import Path

from PIL import Image, ImageChops


FIELDS = {
    "source_turn", "before_image", "after_image", "before_sequence",
    "after_sequence", "crop_box", "inspection_turns",
}


def _image(runtime, name):
    path = Path(runtime) / Path(name).name
    if not path.is_file():
        raise ValueError("effect image unavailable")
    with Image.open(path) as opened:
        return opened.convert("RGB")


def _mask(left, right, threshold):
    difference = ImageChops.difference(left, right)
    return [max(pixel) > threshold for pixel in difference.getdata()]


def _bbox(mask, width):
    indices = [index for index, changed in enumerate(mask) if changed]
    if not indices:
        return None
    xs = [index % width for index in indices]
    ys = [index // width for index in indices]
    return [min(xs), min(ys), max(xs) + 1, max(ys) + 1]


def build(effect, latest_image, runtime_dir, threshold=20, substantial_pixels=1000):
    if type(effect) is not dict or set(effect) != FIELDS:
        raise ValueError("exact effect memory fields required")
    if type(threshold) is not int or not 0 <= threshold <= 255:
        raise ValueError("integer RGB threshold 0..255 required")
    if type(substantial_pixels) is not int or substantial_pixels < 1:
        raise ValueError("positive substantial-pixel threshold required")
    box = effect["crop_box"]
    if type(box) is not list or len(box) != 4 or any(type(value) is not int for value in box):
        raise ValueError("integer crop box required")
    before = _image(runtime_dir, effect["before_image"])
    after = _image(runtime_dir, effect["after_image"])
    latest = _image(runtime_dir, latest_image)
    if before.size != after.size or after.size != latest.size:
        raise ValueError("effect frame sizes differ")
    left, top, right, bottom = box
    if not (0 <= left < right <= before.width and 0 <= top < bottom <= before.height):
        raise ValueError("effect crop outside frame")
    before_crop = before.crop(box)
    after_crop = after.crop(box)
    latest_crop = latest.crop(box)
    after_mask = _mask(before_crop, after_crop, threshold)
    latest_mask = _mask(before_crop, latest_crop, threshold)
    persistent = [first and second for first, second in zip(after_mask, latest_mask)]
    persistent_pixels = sum(persistent)
    crop_pixels = before_crop.width * before_crop.height
    substantial = persistent_pixels >= substantial_pixels
    return {
        "format": "persistent-effect-receipt-v1",
        "source_turn": effect["source_turn"],
        "before_sequence": effect["before_sequence"],
        "after_sequence": effect["after_sequence"],
        "latest_inspection": effect["inspection_turns"],
        "crop_box": box,
        "rgb_difference_threshold": threshold,
        "after_changed_pixels": sum(after_mask),
        "latest_changed_pixels": sum(latest_mask),
        "persistent_changed_pixels": persistent_pixels,
        "crop_pixels": crop_pixels,
        "persistent_fraction": persistent_pixels / crop_pixels,
        "persistent_bbox_in_crop": _bbox(persistent, before_crop.width),
        "classification": (
            "substantial_persistent_visual_change" if substantial
            else "limited_or_transient_visual_change"
        ),
        "semantic_authority": "none",
        "permits_new_mutation": False,
        "limit": "pixel persistence does not prove the intended application effect, target, connectivity or task completion",
    }
