"""Measurement adapter, not the full runtime.

_target and capture are verbatim methods from backend.py blob
9cae101a219348077668c8fc086acf8e13154afe. Constructor and sink are local
instrumentation. No input/admission/manifest method is imported or invoked.
"""
import hashlib
import time
from typing import Any
from Xlib import X

class X11BackendError(RuntimeError):
    pass

class CaptureAdapter:
    def __init__(self, connection, window, sink):
        self.d = connection
        self.root = connection.screen().root
        self.targets = {"target": window}
        self.capture_artifacts = sink

    def _target(self, name: str):
        if name not in self.targets:
            raise X11BackendError(f"unknown target {name}")
        return self.targets[name]

    def capture(self, target: str, frame: str, x: int, y: int, w: int, h: int) -> dict[str, Any]:
        win = self._target(target)
        if frame == "window_client":
            source, sx, sy = win, x, y
        elif frame == "screen_physical_px":
            source, sx, sy = self.root, x, y
        else:
            raise X11BackendError(f"unsupported capture frame {frame}")
        capture_started_ns = time.monotonic_ns()
        image = source.get_image(sx, sy, w, h, X.ZPixmap, 0xFFFFFFFF)
        capture_ended_ns = time.monotonic_ns()
        if image is None:
            raise X11BackendError("capture returned no image")
        raw = bytes(image.data)
        row = {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest(), "width": w, "height": h}
        if self.capture_artifacts is not None:
            row.update(target=target, native_window_id=win.id, frame=frame,
                       region=[x, y, w, h], capture_started_ns=capture_started_ns,
                       capture_ended_ns=capture_ended_ns)
            try:
                info = self.d.display.info
                fmt = next(f for f in info.pixmap_formats if f.depth == image.depth)
                visual = next(v for screen in info.roots for d in screen.allowed_depths
                              for v in d.visuals if v.visual_id == image.visual)
                row["artifact"] = self.capture_artifacts.write(
                    raw, w, h, depth=image.depth, bits_per_pixel=fmt.bits_per_pixel,
                    scanline_pad=fmt.scanline_pad, byte_order=info.image_byte_order,
                    masks=(visual.red_mask, visual.green_mask, visual.blue_mask),
                    true_color=visual.visual_class == X.TrueColor)
            except Exception as error:
                # Keep the actual observation and completed input evidence even
                # if image presentation fails. Never take a replacement capture.
                row["artifact_error"] = repr(error)
        return row
