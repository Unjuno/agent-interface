"""Optional PNG artifacts from the exact X11 GetImage reply already captured."""
from __future__ import annotations

import hashlib
import io
from pathlib import Path
import uuid


class CaptureArtifacts:
    def __init__(self, directory):
        from PIL import Image
        self.image = Image
        self.directory = Path(directory).resolve()
        self.directory.mkdir(parents=True, exist_ok=True)

    def write(self, raw, width, height, *, depth, bits_per_pixel,
              scanline_pad, byte_order, masks, true_color):
        # Do not guess how an unsupported server encodes its pixel data.
        if (depth != 24 or bits_per_pixel != 32 or scanline_pad != 32 or
                byte_order not in (0, 1) or not true_color or
                tuple(masks) != (0xff0000, 0x00ff00, 0x0000ff)):
            raise ValueError("unsupported X11 artifact pixel format")
        if len(raw) != width * height * 4:
            raise ValueError("X11 artifact pixel length mismatch")
        mode = "BGRX" if byte_order == 0 else "XRGB"
        image = self.image.frombytes("RGB", (width, height), raw, "raw", mode)
        encoded = io.BytesIO()
        image.save(encoded, format="PNG")
        data = encoded.getvalue()
        path = self.directory / (uuid.uuid4().hex + ".png")
        with path.open("xb") as handle:
            handle.write(data)
        return {"mime_type": "image/png", "path": str(path),
                "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data),
                "width": width, "height": height,
                "source_raw_sha256": hashlib.sha256(raw).hexdigest()}
