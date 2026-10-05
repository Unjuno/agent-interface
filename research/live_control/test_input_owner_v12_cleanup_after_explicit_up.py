"""An unverified explicit key-up remains retryable during owner cleanup."""
import sys
import threading
import types
import unittest
from pathlib import Path

LIVE = Path(__file__).resolve().parent
sys.path.insert(0, str(LIVE))


class FakeDisplay:
    def __init__(self):
        self.down = set()
        self.release_attempts = 0
        self.root = types.SimpleNamespace(
            query_pointer=lambda: types.SimpleNamespace(mask=0, root_x=0, root_y=0))

    def get_input_focus(self):
        return types.SimpleNamespace(focus=41)

    def keysym_to_keycode(self, _keysym):
        return 65

    def screen(self):
        return types.SimpleNamespace(root=self.root)

    def query_keymap(self):
        bitmap = bytearray(32)
        for code in self.down:
            bitmap[code // 8] |= 1 << (code % 8)
        return bytes(bitmap)

    def sync(self):
        pass

    def close(self):
        pass


class Lease:
    def __init__(self):
        self.deadline = 2**62
        self.cancel = threading.Event()
        self.expected_focus = 41
        self.focus_invalid = False
        self.interrupted = threading.Event()

    def check(self):
        pass

    def record_interruption(self, _row):
        self.interrupted.set()


class ExplicitUpCleanupTests(unittest.TestCase):
    def test_owner_retries_keyup_after_sync_left_key_down(self):
        names = ("Xlib", "Xlib.X", "Xlib.XK", "Xlib.display", "Xlib.error",
                 "Xlib.ext", "Xlib.ext.xtest", "executor_v3")
        saved = {name: sys.modules.get(name) for name in names}
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
                display_instance.release_attempts += 1
                if display_instance.release_attempts > 1:
                    display_instance.down.discard(code)

        xtest.fake_input = fake_input
        ext.xtest = xtest
        xlib.XK, xlib.display, xlib.error, xlib.ext = xk, display, error, ext
        sys.modules.update({"Xlib": xlib, "Xlib.X": types.ModuleType("Xlib.X"),
                            "Xlib.XK": xk, "Xlib.display": display,
                            "Xlib.error": error, "Xlib.ext": ext,
                            "Xlib.ext.xtest": xtest})
        exceptions = types.ModuleType("executor_v3")
        exceptions.Cancelled = type("Cancelled", (Exception,), {})
        exceptions.DecisionRequired = type("DecisionRequired", (Exception,), {})
        sys.modules["executor_v3"] = exceptions
        sys.modules.pop("input_owner_v12", None)
        owner = None
        try:
            from input_owner_v12 import InputOwner

            owner = InputOwner(":fake")
            lease = Lease()
            owner.call("down", lease, "A")
            owner.call("up", lease, "A")
            self.assertEqual(display_instance.down, {65})

            result = owner.call("release", lease)

            self.assertTrue(result["verified"])
            self.assertEqual(result["keys_down"], [])
            self.assertEqual(display_instance.down, set())
            self.assertEqual(display_instance.release_attempts, 2)
        finally:
            if owner is not None:
                owner.close()
            sys.modules.pop("input_owner_v12", None)
            for name, module in saved.items():
                if module is None:
                    sys.modules.pop(name, None)
                else:
                    sys.modules[name] = module


if __name__ == "__main__":
    unittest.main(verbosity=2)
