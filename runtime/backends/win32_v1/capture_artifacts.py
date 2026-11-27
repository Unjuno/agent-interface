"""Optional PNG artifacts from the exact Win32 GDI capture bytes."""
from __future__ import annotations

import hashlib
import binascii
import struct
import time
import uuid
import zlib
from pathlib import Path

MAX_IMAGE_DIMENSION = 8192
MAX_IMAGE_PIXELS = 16_777_216


class CaptureArtifacts:
    def __init__(self, directory, *, retain_rgb=False):
        if type(retain_rgb) is not bool:
            raise ValueError("retain_rgb must be boolean")
        if retain_rgb:
            raise ValueError("Win32 capture artifacts do not retain RGB handoff state")
        self.directory = Path(directory).resolve()
        self.directory.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _encode_png(raw, width, height):
        rows = bytearray()
        for y in range(height):
            rows.append(0)  # PNG filter: None
            start = y * width * 4
            for offset in range(start, start + width * 4, 4):
                blue, green, red = raw[offset:offset + 3]
                rows.extend((red, green, blue))

        def chunk(kind, data):
            body = kind + data
            return (struct.pack(">I", len(data)) + body
                    + struct.pack(">I", binascii.crc32(body) & 0xffffffff))

        converted_ns = time.monotonic_ns()
        header = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
        data = (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", header)
                + chunk(b"IDAT", zlib.compress(rows)) + chunk(b"IEND", b""))
        return data, converted_ns, time.monotonic_ns()

    def write(self, raw, width, height):
        if (type(width) is not int or type(height) is not int
                or width <= 0 or height <= 0
                or width > MAX_IMAGE_DIMENSION or height > MAX_IMAGE_DIMENSION
                or width * height > MAX_IMAGE_PIXELS
                or len(raw) != width * height * 4):
            raise ValueError("Win32 artifact pixel dimensions mismatch")
        started_ns = time.monotonic_ns()
        # GetDIBits uses top-down 32-bit BI_RGB with B,G,R,unused byte order.
        data, converted_ns, encoded_ns = self._encode_png(raw, width, height)
        path = self.directory / (uuid.uuid4().hex + ".png")
        with path.open("xb") as handle:
            handle.write(data)
        written_ns = time.monotonic_ns()
        return {
            "mime_type": "image/png",
            "path": str(path),
            "sha256": hashlib.sha256(data).hexdigest(),
            "bytes": len(data),
            "width": width,
            "height": height,
            "source_raw_sha256": hashlib.sha256(raw).hexdigest(),
            "timing_ns": {"started": started_ns, "converted": converted_ns,
                          "encoded": encoded_ns, "written": written_ns},
        }
