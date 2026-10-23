"""Optional PNG artifacts from the exact Win32 GDI capture bytes."""
from __future__ import annotations

import hashlib
import io
import time
import uuid
from pathlib import Path


class CaptureArtifacts:
    def __init__(self, directory, *, retain_rgb=False):
        if type(retain_rgb) is not bool:
            raise ValueError("retain_rgb must be boolean")
        if retain_rgb:
            raise ValueError("Win32 capture artifacts do not retain RGB handoff state")
        self.directory = Path(directory).resolve()
        self.directory.mkdir(parents=True, exist_ok=True)
        from PIL import Image
        self.image = Image

    def write(self, raw, width, height):
        if (type(width) is not int or type(height) is not int
                or width <= 0 or height <= 0
                or len(raw) != width * height * 4):
            raise ValueError("Win32 artifact pixel dimensions mismatch")
        started_ns = time.monotonic_ns()
        # GetDIBits uses top-down 32-bit BI_RGB with B,G,R,unused byte order.
        image = self.image.frombytes("RGB", (width, height), raw, "raw", "BGRX")
        converted_ns = time.monotonic_ns()
        encoded = io.BytesIO()
        image.save(encoded, format="PNG")
        data = encoded.getvalue()
        encoded_ns = time.monotonic_ns()
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
