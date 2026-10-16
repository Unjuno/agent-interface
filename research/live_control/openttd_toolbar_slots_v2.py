"""Locate the repeated OpenTTD toolbar row without a fixed screen position."""
from pathlib import Path

from PIL import Image

from openttd_toolbar_slots_v1 import SLOT_EDGE_COLOR


def slots_at_row(image, row, minimum_width=20, maximum_width=24):
    pixels = image.load()
    runs = []
    start = None
    for x in range(image.width + 1):
        matched = x < image.width and pixels[x, row] == SLOT_EDGE_COLOR
        if matched and start is None:
            start = x
        elif not matched and start is not None:
            width = x - start
            if minimum_width <= width <= maximum_width:
                runs.append({"box": [start, row, x, row + 23],
                             "point": [(start + x - 1) // 2, row + 11]})
            start = None
    return runs


def discover(image_or_path, minimum_slots=8):
    if isinstance(image_or_path, Image.Image):
        image = image_or_path.convert("RGB")
    else:
        with Image.open(Path(image_or_path)) as opened:
            image = opened.convert("RGB")
    if type(minimum_slots) is not int or minimum_slots < 8:
        raise ValueError("minimum_slots must be an integer of at least eight")
    candidates = []
    for row in range(image.height - 22):
        slots = slots_at_row(image, row)
        if len(slots) >= minimum_slots:
            candidates.append({"row": row, "slots": slots})
    if not candidates:
        raise ValueError("repeated toolbar slot row missing")
    maximum = max(len(candidate["slots"]) for candidate in candidates)
    winners = [candidate for candidate in candidates
               if len(candidate["slots"]) == maximum]
    if len(winners) != 1:
        raise ValueError("repeated toolbar slot row is ambiguous")
    winner = winners[0]
    return {
        "row": winner["row"], "slots": winner["slots"],
        "candidate_rows": [{"row": candidate["row"],
                            "slot_count": len(candidate["slots"])}
                           for candidate in candidates],
        "authority": "screen-derived probe geometry only; grants no semantic or input authority",
    }
