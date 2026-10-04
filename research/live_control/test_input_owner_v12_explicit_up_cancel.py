"""Cancellation arriving inside explicit key-up XSync must not look ordinary."""
import sys
import threading
import types
import unittest
from pathlib import Path

LIVE = Path(__file__).resolve().parent
sys.path.insert(0, str(LIVE))

# Load executor exception types before replacing Xlib with this test's fake server.
import executor_v3


class FakeDisplay:
    def __init__(self):
        self.down = set()
        self.on_sync = None
        self.root = types.SimpleNamespace(
            query_pointer=lambda: types.SimpleNamespace(mask=0, root_x=0, root_y=0))

    def get_input_focus(self):
        return types.SimpleNamespace(focus=41)

    def keysym_to_keycode(self, _keysym):
        return 38

    def screen(self):
        return types.SimpleNamespace(root=self.root)

    def query_keymap(self):
        bitmap = bytearray(32)
        for code in self.down:
            bitmap[code // 8] |= 1 << (code % 8)
        return bytes(bitmap)

    def sync(self):
        if self.on_sync is not None:
            callback, self.on_sync = self.on_sync, None
            callback()

    def close(self):
        pass


class Lease:
    def __init__(self):
        self.deadline = 2**62
        self.cancel = threading.Event()
        self.expected_focus = 41
        self.focus_invalid = False
        self.interrupted = threading.Event()
        self.interruptions = []

    def check(self):
        pass

    def record_interruption(self, row):
        self.interruptions.append(row)
        self.interrupted.set()


class ExplicitKeyUpCancellationTests(unittest.TestCase):
    def test_cancel_during_keyup_sync_is_not_marked_ordinary(self):
        names = ("Xlib", "Xlib.X", "Xlib.XK", "Xlib.display", "Xlib.error",
                 "Xlib.ext", "Xlib.ext.xtest")
        owner_names = ("input_owner_v12", "input_transition_owner_v3",
                       "input_transition_owner_v4")
        saved = {name: sys.modules.get(name) for name in names}
        saved_owners = {name: sys.modules.get(name) for name in owner_names}
        display_instance = FakeDisplay()
        xlib = types.ModuleType("Xlib")
        xlib.X = types.SimpleNamespace(KeyPress=2, KeyRelease=3, ButtonRelease=5,
                                       Button1Mask=256, AnyPropertyType=0)
        xk = types.ModuleType("Xlib.XK")
        xk.string_to_keysym = lambda _key: 1
        display = types.ModuleType("Xlib.display")
        display.Display = lambda _name: display_instance
        error = types.ModuleType("Xlib.error")
        error.BadWindow = type("BadWindow", (Exception,), {})
        error.BadDrawable = type("BadDrawable", (Exception,), {})
        ext = types.ModuleType("Xlib.ext")
        xtest = types.ModuleType("Xlib.ext.xtest")

        def fake_input(_display, event, code):
            if event == xlib.X.KeyPress:
                display_instance.down.add(code)
            elif event == xlib.X.KeyRelease:
                display_instance.down.discard(code)

        xtest.fake_input = fake_input
        ext.xtest = xtest
        xlib.XK, xlib.display, xlib.error, xlib.ext = xk, display, error, ext
        sys.modules.update({"Xlib": xlib, "Xlib.X": types.ModuleType("Xlib.X"),
                            "Xlib.XK": xk, "Xlib.display": display,
                            "Xlib.error": error, "Xlib.ext": ext,
                            "Xlib.ext.xtest": xtest})
        owner = None
        try:
            for name in owner_names:
                sys.modules.pop(name, None)
            from input_transition_owner_v4 import InputOwner

            owner = InputOwner(":fake")
            lease = Lease()
            owner.call("down", lease, "W")
            display_instance.on_sync = lease.cancel.set
            row = owner.call("up", lease, "W")

            self.assertIsInstance(row, dict)
            self.assertTrue(row["cancel_requested_after_sync"])
            self.assertFalse(row["ordinary_release_candidate"])
            self.assertTrue(lease.interrupted.wait(1))
            self.assertEqual(lease.interruptions[0]["reason"], "cancelled")
        finally:
            if owner is not None:
                owner.close()
            for name, module in saved.items():
                if module is None:
                    sys.modules.pop(name, None)
                else:
                    sys.modules[name] = module
            for name, module in saved_owners.items():
                if module is None:
                    sys.modules.pop(name, None)
                else:
                    sys.modules[name] = module


if __name__ == "__main__":
    unittest.main(verbosity=2)
