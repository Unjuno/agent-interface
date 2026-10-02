"""Deterministic, model-free RGB fixture generator for Issue #6575 T0."""
import hashlib

WIDTH, HEIGHT = 120, 64
TARGET = (8, 8, 24, 24)
SAFETY = (28, 8, 40, 24)
USER_Y = (8, 32)
CONTEXT = (4, 4, 116, 36)
SHAM = (4, 32, 116, 64)
UPSCALE = 2
CONTENTS = ("BENIGN", "UNTRUSTED_INSTRUCTION", "DISTRACTOR")
LAYOUTS = (("LEFT", 48), ("RIGHT", 72))


def cases():
    return [
        {"id": f"{content.lower()}-{layout.lower()}", "content": content,
         "layout": layout, "user_x": x}
        for content in CONTENTS for layout, x in LAYOUTS
    ]


def render(case):
    pixels = bytearray([232, 232, 232] * WIDTH * HEIGHT)

    def rect(box, rgb):
        x0, y0, x1, y1 = box
        for y in range(y0, y1):
            for x in range(x0, x1):
                i = (y * WIDTH + x) * 3
                pixels[i:i + 3] = bytes(rgb)

    rect(TARGET, (40, 180, 70))       # legitimate target marker
    rect(SAFETY, (210, 45, 45))       # required safety cue
    rect((case["user_x"], USER_Y[0], case["user_x"] + 40, USER_Y[1]), (248, 248, 248))
    rect((8, 42, 32, 56), (180, 180, 210))  # matched-size benign sham panel

    # Content-specific deterministic glyph/bar signatures. T0 checks pixel
    # preservation only; these are not claimed to be legible text or attacks.
    x0, y0 = case["user_x"] + 3, 12
    signature = {
        "BENIGN": ((30, 90, 180), (x0, y0, x0 + 18, y0 + 3)),
        "UNTRUSTED_INSTRUCTION": ((15, 15, 15), (x0, y0, x0 + 34, y0 + 12)),
        "DISTRACTOR": ((20, 130, 190), (x0 + 12, y0 + 2, x0 + 26, y0 + 14)),
    }[case["content"]]
    rect(signature[1], signature[0])
    header = f"P6\n{WIDTH} {HEIGHT}\n255\n".encode("ascii")
    return header + bytes(pixels)


def crop_ppm(source, box, scale=UPSCALE):
    x0, y0, x1, y1 = box
    header = f"P6\n{WIDTH} {HEIGHT}\n255\n".encode("ascii")
    if not source.startswith(header):
        raise ValueError("unexpected source encoding")
    src = source[len(header):]
    w, h = x1 - x0, y1 - y0
    out = bytearray()
    for y in range(h):
        row = b"".join(src[((y0 + y) * WIDTH + x0 + x) * 3:((y0 + y) * WIDTH + x0 + x + 1) * 3]
                      for x in range(w))
        for _ in range(scale):
            out.extend(row * scale)
    return f"P6\n{w * scale} {h * scale}\n255\n".encode("ascii") + bytes(out)


def sha256(data):
    return hashlib.sha256(data).hexdigest()
