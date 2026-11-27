"""A failed second key reply retains both possible-DOWN obligations."""
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from Xlib import X
from runtime.backends.x11_v1.backend import X11Backend


class MultiKeyChordReplyBoundaryTests(unittest.TestCase):
    def test_second_key_reply_failure_keeps_both_keys_owned(self):
        backend = object.__new__(X11Backend)
        backend.held_keycodes = {}
        backend.held_buttons = set()
        backend.emissions = 0
        keycodes = {"Shift_L": 50, "a": 38}
        backend._keycode = keycodes.__getitem__

        trace = []
        obligations = []
        backend._input_obligation_publisher = (
            lambda keys, buttons: obligations.append(dict(keys)))
        backend._before_input_press = lambda: trace.append("authority")

        sync_count = 0

        def sync():
            nonlocal sync_count
            sync_count += 1
            trace.append("sync")
            if sync_count == 2:
                raise OSError("second key reply unavailable")

        backend.d = SimpleNamespace(
            sync=sync,
            get_modifier_mapping=lambda: [[50]] + [[] for _ in range(7)],
        )

        def emit(connection, kind, code):
            self.assertIs(connection, backend.d)
            trace.append(("down" if kind == X.KeyPress else "up", code))

        with patch("runtime.backends.x11_v1.backend.xtest.fake_input",
                   side_effect=emit):
            with self.assertRaisesRegex(OSError, "second key reply unavailable"):
                backend.key_chord(["Shift_L", "a"])

        self.assertEqual(trace, [
            "authority", ("down", 50), "sync",
            "authority", ("down", 38), "sync",
        ])
        self.assertEqual(backend.held_keycodes, {"Shift_L": 50, "a": 38})
        self.assertEqual(obligations, [
            {"Shift_L": 50}, {"Shift_L": 50, "a": 38},
        ])
        self.assertEqual(backend.emissions, 2)
        self.assertFalse(getattr(backend, "_tap_defer_sync", False))


if __name__ == "__main__":
    unittest.main()
