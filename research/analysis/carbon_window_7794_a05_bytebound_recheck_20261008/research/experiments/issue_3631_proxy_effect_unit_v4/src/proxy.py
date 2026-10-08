"""Deterministic proxy image and pure representation-specific target derivation."""
from pathlib import Path

BLUE = (44, 110, 170)
FONT = {
    "C": ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    "O": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "U": ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    "N": ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "V": ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "M": ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    "I": ("11111", "00100", "00100", "00100", "00100", "00100", "11111"),
    "0": ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    "1": ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
}


def render(counter: int, version: int, path: Path, button_rect: dict) -> None:
    width, height, scale = 320, 120, 2
    pixels = bytearray([245, 247, 250] * width * height)

    def rect(x, y, w, h, color):
        for yy in range(max(0, y), min(height, y + h)):
            for xx in range(max(0, x), min(width, x + w)):
                i = (yy * width + xx) * 3
                pixels[i:i + 3] = bytes(color)

    def word(s, x, y, color=(28, 38, 54)):
        for char in s:
            bitmap = FONT.get(char)
            if bitmap:
                for ry, row in enumerate(bitmap):
                    for rx, bit in enumerate(row):
                        if bit == "1":
                            rect(x + rx * scale, y + ry * scale, scale, scale, color)
            x += 6 * scale

    word("COUNT", 12, 14)
    word(str(counter), 92, 14, (10, 95, 55))
    word("VERSION", 12, 36, (80, 88, 100))
    word(str(version % 10), 108, 36, (80, 88, 100))
    r = button_rect
    rect(r["x"], r["y"], r["width"], r["height"], BLUE)
    word("INCREMENT", r["x"] + 25, r["y"] + 10, (255, 255, 255))
    path.write_bytes(f"P6\n{width} {height}\n255\n".encode("ascii") + pixels)


def ppm_rgb(data: bytes):
    parts = data.split(b"\n", 3)
    if len(parts) != 4 or parts[0] != b"P6" or parts[2] != b"255":
        raise ValueError("unsupported proxy image format")
    width, height = map(int, parts[1].split())
    rgb = parts[3]
    if len(rgb) != width * height * 3:
        raise ValueError("proxy image length mismatch")
    return width, height, rgb


def blue_bbox(width: int, height: int, rgb: bytes):
    xs, ys = [], []
    for y in range(height):
        for x in range(width):
            offset = (y * width + x) * 3
            red, green, blue = rgb[offset:offset + 3]
            if red < 70 and 80 <= green <= 145 and 130 <= blue <= 205 and blue > red + 70:
                xs.append(x)
                ys.append(y)
    if not xs:
        raise ValueError("representation contains no action target")
    return {"x": min(xs), "y": min(ys), "width": max(xs) - min(xs) + 1,
            "height": max(ys) - min(ys) + 1}


def center(rect):
    return [rect["x"] + rect["width"] // 2, rect["y"] + rect["height"] // 2]
