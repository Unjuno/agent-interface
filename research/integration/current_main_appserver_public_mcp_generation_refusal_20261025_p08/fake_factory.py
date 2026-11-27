"""Deterministic synthetic target UI for the p08 model-grounding trial."""

import hashlib
import json
from pathlib import Path
import time
from unittest.mock import Mock

from PIL import Image, ImageDraw
from Xlib import X

from runtime.cli_v1.mcp_guarded import GuardedSessionOwner
from runtime.cli_v1.test_mcp_owned_process import _Cleanup, _FakeQueries
from runtime.cli_v1.test_mcp_process_identity import FakeX
from unittest.mock import patch


GREEN_RECT = (12, 3, 20, 13)
EFFECT_PIXEL = (1, 1)
TARGET_RGB = (0, 220, 40)
SUCCESS_RGB = (255, 0, 0)


def _write_json(path, value):
    Path(path).write_text(json.dumps(value, sort_keys=True) + "\n",
                          encoding="utf-8", newline="\n")


class GroundingFakeX(FakeX):
    """Fake the X transport while independently scoring the actual pointer event."""

    def __init__(self, cleanup, root):
        self.evidence_root = Path(root)
        self.pointer = (0, 0)
        self.button_events = []
        self.owner_input_events = []
        super().__init__(cleanup)

        image = Image.new("RGB", (32, 32), (24, 24, 24))
        draw = ImageDraw.Draw(image)
        for rect, color, label in (
                ((3, 3, 11, 13), (220, 40, 40), "R"),
                (GREEN_RECT, TARGET_RGB, "G"),
                ((21, 3, 29, 13), (40, 70, 220), "B")):
            draw.rectangle(rect, fill=color, outline=(245, 245, 245), width=1)
            draw.text((rect[0] + 3, rect[1] + 1), label, fill=(255, 255, 255))
        image.putpixel(EFFECT_PIXEL, (31, 29, 1))
        image.putpixel((2, 2), (62, 58, 4))
        self.raw = image.tobytes("raw", "BGRX")
        _write_json(self.evidence_root / "owner-input-events.json", [])

    def read(self, connection, xid):
        if (self.evidence_root / "invalidate-generation-after-provider").is_file():
            self.generation = "b" * 64
        return super().read(connection, xid)

    def emit(self, connection, kind, code=0, *, time=0, root=0, x=0, y=0):
        if kind in (X.KeyPress, X.KeyRelease, X.ButtonPress, X.ButtonRelease):
            event = {"kind": kind, "code": code,
                     "monotonic_ns": time_monotonic_ns()}
            self.owner_input_events.append(event)
            _write_json(self.evidence_root / "owner-input-events.json",
                        self.owner_input_events)
        if kind == X.MotionNotify:
            self.pointer = (x, y)
        elif kind == X.ButtonPress and code == 1:
            point = list(self.pointer)
            event = {"kind": "ButtonPress", "button": code,
                     "point": point, "monotonic_ns": time_monotonic_ns()}
            self.button_events.append(event)
            _write_json(self.evidence_root / "synthetic-target-click.json", {
                "event": event, "target_rect": list(GREEN_RECT),
                "transport_scope": "owner-side XTEST fake-input receipt"})
            if (GREEN_RECT[0] <= point[0] <= GREEN_RECT[2] and
                    GREEN_RECT[1] <= point[1] <= GREEN_RECT[3]):
                image = Image.frombytes("RGB", (32, 32), self.raw, "raw", "BGRX")
                image.putpixel(EFFECT_PIXEL, SUCCESS_RGB)
                self.raw = image.tobytes("raw", "BGRX")
                (self.evidence_root / "synthetic-application-state.rgb").write_bytes(
                    self.raw)
                _write_json(self.evidence_root / "synthetic-effect-receipt.json", {
                    "event": "synthetic_app_green_target_effect",
                    "monotonic_ns": time_monotonic_ns(),
                    "click_point": point, "pixel": list(EFFECT_PIXEL),
                    "rgb": list(SUCCESS_RGB),
                    "button_press_count": len(self.button_events)})
        return super().emit(connection, kind, code)


def time_monotonic_ns():
    return time.monotonic_ns()


def grounding_fake_owner_factory(targets, directory, display_name, options):
    root = Path(directory)
    cleanup = _Cleanup()
    fake = GroundingFakeX(cleanup, root)
    fake.backend.d.get_display_name = lambda: "fake-display"
    fake.backend.d.display = type("DisplayInfo", (), {
        "info": type("Info", (), {"resource_id_base": 0x1200000})()})()
    fake.backend.root.query_pointer = lambda: type("PointerState", (), {
        "mask": 0, "root_x": fake.pointer[0], "root_y": fake.pointer[1]})()
    fake.backend.close = Mock()
    if (root / "compiled-profile-mode").exists():
        (root / "synthetic-application-initial.rgb").write_bytes(fake.raw)

    for target, kwargs in (
            ("runtime.guarded_x11_v1.bridge._GuardedBackend",
             {"return_value": fake.backend}),
            ("runtime.guarded_x11_v1.bridge.read_linux_x11_process_identity",
             {"side_effect": fake.read}),
            ("runtime.backends.x11_v1.backend.xtest.fake_input",
             {"side_effect": fake.emit}),
            ("runtime.guarded_x11_v1.target_queries.X11TargetQueries",
             {"return_value": _FakeQueries(root)})):
        patcher = patch(target, **kwargs)
        patcher.start()
        cleanup.addCleanup(patcher.stop)

    owner = GuardedSessionOwner(targets, directory, display_name, **options)
    owner._owned_process_test_cleanup = cleanup
    return owner
