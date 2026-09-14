"""Derive the visible 4x4 Mindustry build palette from lower-right screen edges."""
from pathlib import Path

from PIL import Image


X_OFFSETS = [42, 88, 132, 177]
Y_OFFSETS = [32, 78, 124, 170]


def discover(image_or_path):
    if isinstance(image_or_path, Image.Image):
        image = image_or_path.convert("L")
    else:
        with Image.open(Path(image_or_path)) as opened:
            image = opened.convert("L")
    width, height = image.size
    pixels = image.load()
    x_start, x_stop = int(width * .70), int(width * .82)
    y_start, y_stop = int(height * .64), int(height * .76)
    vertical_band = range(int(height * .66), int(height * .95))
    horizontal_band = range(int(width * .70), int(width * .96))
    x_scores = [(sum(abs(pixels[x + 1, y] - pixels[x, y]) for y in vertical_band), x)
                for x in range(x_start, x_stop)]
    y_scores = [(sum(abs(pixels[x, y + 1] - pixels[x, y]) for x in horizontal_band), y)
                for y in range(y_start, y_stop)]
    x_score, left = max(x_scores)
    y_score, top = max(y_scores)
    if x_score < 10000 or y_score < 10000:
        raise ValueError("Mindustry palette boundary evidence too weak")
    if left + X_OFFSETS[-1] >= width or top + Y_OFFSETS[-1] >= height:
        raise ValueError("derived Mindustry palette exceeds source image")
    slots = []
    for row, y_offset in enumerate(Y_OFFSETS):
        for column, x_offset in enumerate(X_OFFSETS):
            slots.append({"row": row, "column": column,
                          "point": [left + x_offset, top + y_offset]})
    return {"boundary": {"left": left, "top": top,
                         "vertical_edge_score": x_score,
                         "horizontal_edge_score": y_score},
            "slots": slots,
            "tooltip_box": [left + 1, top - 100, width, top],
            "authority": "screen-derived palette probe geometry only; grants no semantic or input authority"}


def nearest(point, slots):
    if (not isinstance(point, list) or len(point) != 2
            or any(type(value) is not int for value in point)):
        raise ValueError("integer source point required")
    index = min(range(len(slots)), key=lambda item:
                (slots[item]["point"][0] - point[0]) ** 2
                + (slots[item]["point"][1] - point[1]) ** 2)
    return {"slot_index": index, "point": slots[index]["point"],
            "source_point": point,
            "authority": "nearest screen-derived probe only; grants no input authority"}
