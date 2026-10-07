"""Optional PNG from the same top-down 32-bit BI_RGB capture bytes."""
from __future__ import annotations
import hashlib
from pathlib import Path
import struct
import uuid
import zlib

class CaptureArtifacts:
    def __init__(self, directory):
        self.directory = Path(directory).resolve()
        self.directory.mkdir(parents=True, exist_ok=True)

    def write(self, raw, width, height):
        if (type(raw) is not bytes or type(width) is not int or type(height) is not int
                or not 1 <= width <= 8192 or not 1 <= height <= 8192
                or width * height > 16_777_216 or len(raw) != width * height * 4):
            raise ValueError("invalid Win32 BI_RGB pixel buffer")
        # BI_RGB DIB alpha is unspecified; PNG stores the observed RGB channels.
        rows = bytearray()
        for y in range(height):
            rows.append(0)  # PNG filter None.
            row = raw[y * width * 4:(y + 1) * width * 4]
            rgb = bytearray(width * 3)
            rgb[0::3] = row[2::4]
            rgb[1::3] = row[1::4]
            rgb[2::3] = row[0::4]
            rows.extend(rgb)
        def chunk(kind, payload):
            return (struct.pack(">I", len(payload)) + kind + payload
                    + struct.pack(">I", zlib.crc32(kind + payload) & 0xffffffff))
        data = (b"\x89PNG\r\n\x1a\n"
                + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
                + chunk(b"IDAT", zlib.compress(rows)) + chunk(b"IEND", b""))
        path = self.directory / (uuid.uuid4().hex + ".png")
        with path.open("xb") as handle:
            handle.write(data)
        return {"mime_type": "image/png", "path": str(path),
                "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data),
                "width": width, "height": height,
                "source_raw_sha256": hashlib.sha256(raw).hexdigest()}
