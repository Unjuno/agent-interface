"""Minimal P6 PPM helpers for deterministic, dependency-free fixtures."""
from __future__ import annotations


def encode(width: int, height: int, pixels: bytes) -> bytes:
    if width <= 0 or height <= 0 or len(pixels) != width * height * 3:
        raise ValueError("invalid PPM dimensions/pixel length")
    return f"P6\n{width} {height}\n255\n".encode("ascii") + pixels


def decode(raw: bytes) -> tuple[int, int, bytes]:
    parts = raw.split(b"\n", 3)
    if len(parts) != 4 or parts[0] != b"P6" or parts[2] != b"255":
        raise ValueError("unsupported PPM header")
    width, height = (int(v) for v in parts[1].split())
    pixels = parts[3]
    if width <= 0 or height <= 0 or len(pixels) != width * height * 3:
        raise ValueError("invalid PPM dimensions/pixel length")
    return width, height, pixels


def crop(raw: bytes, rect: list[int]) -> bytes:
    width, height, pixels = decode(raw)
    x0, y0, x1, y1 = rect
    if not (0 <= x0 < x1 <= width and 0 <= y0 < y1 <= height):
        raise ValueError("crop outside source")
    rows = [pixels[(y * width + x0) * 3:(y * width + x1) * 3]
            for y in range(y0, y1)]
    return encode(x1 - x0, y1 - y0, b"".join(rows))
