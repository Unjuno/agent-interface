"""Exact declared visual pattern; no inference from unseen scheduled cues."""


def decode(pixels):
    if not isinstance(pixels, list) or len(pixels) != 1024:
        return None
    if any(type(x) is not int for x in pixels):
        return None
    identity, color = pixels[0], pixels[1]
    if identity not in range(1, 9) or color not in (0xFF0000, 0x00FF00):
        return None
    if any(x != color for x in pixels[1:]):
        return None
    return {"id": identity, "color": color}


def capture_slots(offsets):
    if len(offsets) != 4 or any(type(x) is not int or not 0 <= x < 12 for x in offsets):
        raise ValueError("four integer phase offsets in [0,12) required")
    return [120 * k + 10 * offsets[k % 4] + 5 for k in range(8)]
