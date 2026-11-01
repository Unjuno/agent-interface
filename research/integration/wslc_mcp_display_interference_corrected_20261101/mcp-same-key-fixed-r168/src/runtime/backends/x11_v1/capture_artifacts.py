"""Optional PNG artifacts from the exact X11 GetImage reply already captured."""
from __future__ import annotations

import copy
import hashlib
import io
import time
from pathlib import Path
import uuid


class CaptureArtifacts:
    def __init__(self, directory, *, retain_rgb=False):
        if type(retain_rgb) is not bool:
            raise ValueError("retain_rgb must be boolean")
        self.retain_rgb = retain_rgb
        self._pending_rgb = None
        from PIL import Image
        self.image = Image
        self.directory = Path(directory).resolve()
        self.directory.mkdir(parents=True, exist_ok=True)

    def write(self, raw, width, height, *, depth, bits_per_pixel,
              scanline_pad, byte_order, masks, true_color):
        self.discard_rgb()
        # Do not guess how an unsupported server encodes its pixel data.
        if (depth != 24 or bits_per_pixel != 32 or scanline_pad != 32 or
                byte_order not in (0, 1) or not true_color or
                tuple(masks) != (0xff0000, 0x00ff00, 0x0000ff)):
            raise ValueError("unsupported X11 artifact pixel format")
        if len(raw) != width * height * 4:
            raise ValueError("X11 artifact pixel length mismatch")
        started_ns = time.monotonic_ns()
        mode = "BGRX" if byte_order == 0 else "XRGB"
        image = self.image.frombytes("RGB", (width, height), raw, "raw", mode)
        converted_ns = time.monotonic_ns()
        encoded = io.BytesIO()
        image.save(encoded, format="PNG")
        data = encoded.getvalue()
        encoded_ns = time.monotonic_ns()
        path = self.directory / (uuid.uuid4().hex + ".png")
        with path.open("xb") as handle:
            handle.write(data)
        written_ns = time.monotonic_ns()
        data_sha256 = hashlib.sha256(data).hexdigest()
        raw_sha256 = hashlib.sha256(raw).hexdigest()
        hashed_ns = time.monotonic_ns()
        row = {"mime_type": "image/png", "path": str(path),
                "sha256": data_sha256, "bytes": len(data),
                "width": width, "height": height,
                "source_raw_sha256": raw_sha256,
                # Same-process monotonic brackets; write/close does not imply fsync.
                "timing_ns": {"started": started_ns, "converted": converted_ns,
                              "encoded": encoded_ns, "written": written_ns,
                              "hashed": hashed_ns}}

        if self.retain_rgb:
            self._pending_rgb = (copy.deepcopy(row), image)
        return row

    def discard_rgb(self):
        """Bound the private handoff to one completed capture, never a cache."""
        self._pending_rgb = None

    def take_rgb(self, artifact):
        """Consume the exact PNG producer's RGB image once, or refuse.

        The caller still verifies the saved PNG bytes and raw-capture link. This
        handoff neither captures again nor accepts any older artifact identity.
        """
        pending = self._pending_rgb
        self.discard_rgb()
        if pending is None or artifact != pending[0]:
            raise ValueError("no matching current capture RGB handoff")
        return pending[1]
