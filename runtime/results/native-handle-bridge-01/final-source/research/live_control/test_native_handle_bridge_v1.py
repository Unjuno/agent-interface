import tempfile
import time
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from PIL import Image
from native_handle_bridge_v1 import NativeHandleBridge, _GuardedBackend
from scoped_target_handle_v3 import TargetHandleStore
from runtime.backends.x11_v1.backend import X11Backend, X11BackendError


class NativeHandleBridgeTests(unittest.TestCase):
    def test_existing_store_refuses_changed_pixels_at_native_check(self):
        bridge = object.__new__(NativeHandleBridge)
        bridge.scope = "test-session"
        bridge.store = TargetHandleStore(bridge.scope)
        bridge.sequence = 2
        bridge.active = ("field", [4, 4])
        bridge.deadline = None
        bridge.checks = []
        image = Image.new("RGB", (40, 40), "white")
        for y in range(8, 16):
            for x in range(8, 16):
                image.putpixel((x, y), (0, 0, 0) if (x+y)%2 else (255, 255, 255))
        now = time.monotonic_ns()
        obs = {"sequence": 1, "capture_ns": now,
               "pointer_binding": {"focus": 20, "surface": 20, "geometry": [0, 0, 40, 40]}}
        bridge.store.mint("field", "window_content", [8, 8, 8, 8], obs, image, now)
        current = dict(obs, sequence=2)
        bridge.history = {2: (current, image)}
        bridge.observe = lambda: current
        self.assertEqual(bridge.check("before_press")["point"], [12, 12])
        changed = image.copy()
        changed.putpixel((8, 8), (100, 100, 100))
        bridge.history[2] = (current, changed)
        with self.assertRaises(X11BackendError):
            bridge.check("before_press")
        self.assertEqual(bridge.checks[-1]["status"], "MISSING")

    def test_point_change_after_move_prevents_native_press(self):
        backend = object.__new__(_GuardedBackend)
        backend.owner = SimpleNamespace(check=mock.Mock(return_value={"point": [50, 50]}), moved_point=[40, 40])
        backend.root = SimpleNamespace(query_pointer=lambda: SimpleNamespace(root_x=40, root_y=40))
        with mock.patch.object(X11Backend, "pointer_button") as press:
            with self.assertRaises(X11BackendError):
                backend.pointer_button("left", True)
            press.assert_not_called()

    def test_release_is_not_blocked_by_guard_refusal(self):
        backend = object.__new__(_GuardedBackend)
        backend.owner = SimpleNamespace(check=mock.Mock(side_effect=X11BackendError("stale")))
        with mock.patch.object(X11Backend, "pointer_button") as release:
            backend.pointer_button("left", False)
            release.assert_called_once_with("left", False)
            backend.owner.check.assert_not_called()

    def test_expired_guard_does_not_capture_or_resolve(self):
        bridge = object.__new__(NativeHandleBridge)
        bridge.active = ("field", [1, 1])
        bridge.deadline = 1
        bridge.observe = mock.Mock()
        with self.assertRaises(X11BackendError):
            bridge.check("before_press")
        bridge.observe.assert_not_called()

    def test_refusal_before_admission_never_dispatches(self):
        with tempfile.TemporaryDirectory() as tmp:
            bridge = object.__new__(NativeHandleBridge)
            bridge.out = Path(tmp)
            bridge.active = None
            bridge.check = mock.Mock(side_effect=X11BackendError("changed target"))
            bridge.session = SimpleNamespace(dispatch=mock.Mock())
            row = bridge.click("field", [1, 1])
            self.assertEqual(row["status"], "refused")
            self.assertFalse(row["input_dispatched"])
            bridge.session.dispatch.assert_not_called()
            self.assertIsNone(bridge.active)

    def test_mint_requires_explicit_retained_source(self):
        bridge = object.__new__(NativeHandleBridge)
        bridge.history = {}
        with self.assertRaises(KeyError):
            bridge.mint("field", 123, [10, 10])


if __name__ == "__main__":
    unittest.main()
