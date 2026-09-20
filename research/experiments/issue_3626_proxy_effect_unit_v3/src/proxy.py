"""Small task-specific image proxy renderer; intentionally not a general GUI."""
from pathlib import Path

FONT = {
    "C": ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    "O": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "U": ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    "N": ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "I": ("11111", "00100", "00100", "00100", "00100", "00100", "11111"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "M": ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    "V": ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "S": ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    "0": ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    "1": ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
}


def render(counter: int, version: int, path: Path) -> None:
    width, height, scale = 320, 120, 3
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

    word("COUNT", 22, 20)
    word(str(counter), 148, 20, (10, 95, 55))
    word("VERSION", 22, 52, (80, 88, 100))
    word(str(version % 10), 148, 52, (80, 88, 100))
    rect(185, 78, 112, 28, (40, 110, 190))
    word("INCREMENT", 190, 87, (255, 255, 255))
    header = f"P6\n{width} {height}\n255\n".encode("ascii")
    path.write_bytes(header + pixels)
