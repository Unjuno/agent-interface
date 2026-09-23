"""Discover repeated OpenTTD toolbar slots without assigning semantic meaning."""
from pathlib import Path

from PIL import Image


SLOT_EDGE_COLOR = (168, 168, 168)


def discover(image_or_path, row=40, minimum_width=20, maximum_width=24):
    if isinstance(image_or_path, Image.Image):
        image = image_or_path.convert("RGB")
    else:
        with Image.open(Path(image_or_path)) as opened:
            image = opened.convert("RGB")
    if not 0 <= row < image.height:
        raise ValueError("toolbar row outside image")
    matches = [image.getpixel((x, row)) == SLOT_EDGE_COLOR for x in range(image.width)]
    runs = []
    start = None
    for x, matched in enumerate(matches + [False]):
        if matched and start is None:
            start = x
        elif not matched and start is not None:
            width = x - start
            if minimum_width <= width <= maximum_width:
                runs.append({"box": [start, row, x, row + 23],
                             "point": [(start + x - 1) // 2, row + 11]})
            start = None
    if len(runs) < 8:
        raise ValueError("repeated toolbar slot structure missing")
    return runs


def expand(points, slots, margin=1, maximum_span=7):
    if not points or not slots or type(margin) is not int or margin < 0:
        raise ValueError("points, slots and non-negative margin required")
    indexes = []
    for point in points:
        if (not isinstance(point, (list, tuple)) or len(point) != 2
                or type(point[0]) is not int or type(point[1]) is not int):
            raise ValueError("integer candidate point required")
        indexes.append(min(range(len(slots)),
                           key=lambda index: abs(slots[index]["point"][0] - point[0])))
    left = max(0, min(indexes) - margin)
    right = min(len(slots) - 1, max(indexes) + margin)
    if right - left + 1 > maximum_span:
        raise ValueError("model candidate span too broad for bounded expansion")
    return {"slot_indexes": list(range(left, right + 1)),
            "points": [slots[index]["point"] for index in range(left, right + 1)],
            "model_candidate_slot_indexes": indexes,
            "margin": margin,
            "maximum_span": maximum_span,
            "authority": "screen-derived probe candidates only; grants no input authority"}


def local_neighbourhood(anchor_point, slots, radius=2):
    if (not isinstance(anchor_point, (list, tuple)) or len(anchor_point) != 2
            or type(anchor_point[0]) is not int or type(anchor_point[1]) is not int):
        raise ValueError("integer anchor point required")
    if not slots or type(radius) is not int or radius < 1:
        raise ValueError("slots and positive integer radius required")
    anchor = min(range(len(slots)),
                 key=lambda index: abs(slots[index]["point"][0] - anchor_point[0]))
    left = max(0, anchor - radius)
    right = min(len(slots) - 1, anchor + radius)
    return {"anchor_slot_index": anchor,
            "slot_indexes": list(range(left, right + 1)),
            "points": [slots[index]["point"] for index in range(left, right + 1)],
            "radius": radius,
            "authority": "screen-derived local probe candidates only; grants no input authority"}
