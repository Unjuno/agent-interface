"""Create two deterministic 1x1 RGB PNGs used only by the loopback probe."""

from __future__ import annotations

import binascii
import struct
import zlib
from pathlib import Path


def _chunk(kind: bytes, payload: bytes) -> bytes:
    body = kind + payload
    return struct.pack(">I", len(payload)) + body + struct.pack(">I", binascii.crc32(body) & 0xFFFFFFFF)


def _png(rgb: tuple[int, int, int]) -> bytes:
    raw = b"\x00" + bytes(rgb)
    return (
        b"\x89PNG\r\n\x1a\n"
        + _chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0))
        + _chunk(b"IDAT", zlib.compress(raw))
        + _chunk(b"IEND", b"")
    )


def _read_single_pixel(data: bytes) -> tuple[int, int, int]:
    if not data.startswith(b"\x89PNG\r\n\x1a\n"):
        raise ValueError("invalid PNG signature")
    offset = 8
    compressed = bytearray()
    while offset < len(data):
        size = struct.unpack_from(">I", data, offset)[0]
        kind = data[offset + 4:offset + 8]
        payload = data[offset + 8:offset + 8 + size]
        crc = struct.unpack_from(">I", data, offset + 8 + size)[0]
        if (binascii.crc32(kind + payload) & 0xFFFFFFFF) != crc:
            raise ValueError("PNG chunk CRC mismatch")
        if kind == b"IDAT":
            compressed.extend(payload)
        offset += size + 12
        if kind == b"IEND":
            break
    decoded = zlib.decompress(compressed)
    if len(decoded) != 4 or decoded[0] != 0:
        raise ValueError("unexpected one-pixel RGB scanline")
    return tuple(decoded[1:])


def main() -> None:
    output = Path(__file__).with_name("fixtures")
    output.mkdir(exist_ok=True)
    for sequence, rgb in ((201, (213, 32, 32)), (202, (32, 64, 213))):
        data = _png(rgb)
        if _read_single_pixel(data) != rgb:
            raise ValueError("generated PNG did not round-trip")
        (output / f"synthetic-seq{sequence}.png").write_bytes(data)


if __name__ == "__main__":
    main()
