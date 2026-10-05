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
        self.buttons_down = set()
        self.release_attempts = 0
        self.button_release_attempts = 0
        self.drop_next_key_release = True
        self.drop_next_button_release = True
        self.root = FakeRoot(self)

    def get_input_focus(self):
        return types.SimpleNamespace(focus=41)

    def keysym_to_keycode(self, _keysym):
        return 65

    def screen(self):
        return types.SimpleNamespace(root=self.root)

    def create_resource_object(self, _kind, window_id):
        parent = FakeWindow(self, 52)
        return FakeWindow(self, window_id, parent=parent if window_id == 41 else None)

    def intern_atom(self, _name):
        return 1

    def query_keymap(self):
        bitmap = bytearray(32)
        for code in self.down:
            bitmap[code // 8] |= 1 << (code % 8)
        return bytes(bitmap)

    def sync(self):
        pass

    def close(self):
        pass


class FakeWindow:
    def __init__(self, display, window_id, parent=None):
        self.display = display
        self.id = window_id
        self.parent = parent

    def get_geometry(self):
        return types.SimpleNamespace(width=100, height=100)

    def get_attributes(self):
        return types.SimpleNamespace(map_state=2)

    def query_tree(self):
        return types.SimpleNamespace(parent=self.parent)


class FakeRoot:
    id = 1

    def __init__(self, display):
        self.display = display

    def query_pointer(self):
        mask = sum(256 << (button - 1) for button in self.display.buttons_down)
        return types.SimpleNamespace(mask=mask, root_x=0, root_y=0)

    def get_full_property(self, _atom, _property_type):
        return types.SimpleNamespace(value=[52])

    def translate_coords(self, source, x, y):
        if isinstance(source, FakeRoot):
            return types.SimpleNamespace(child=FakeWindow(self.display, 52), x=x, y=y)
        return types.SimpleNamespace(child=None, x=0, y=0)


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
    def test_owner_retries_dropped_button_up_during_cleanup(self):
        names = ("Xlib", "Xlib.X", "Xlib.XK", "Xlib.display", "Xlib.error",
                 "Xlib.ext", "Xlib.ext.xtest", "executor_v3")
        saved = {name: sys.modules.get(name) for name in names}
        display_instance = FakeDisplay()
        xlib = types.ModuleType("Xlib")
        xlib.X = types.SimpleNamespace(KeyPress=2, KeyRelease=3, ButtonPress=4,
                                       ButtonRelease=5, Button1Mask=256,
                                       AnyPropertyType=0, IsViewable=2)
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
                if display_instance.drop_next_key_release:
                    display_instance.drop_next_key_release = False
                else:
                    display_instance.down.discard(code)
            elif event == xlib.X.ButtonPress:
                display_instance.buttons_down.add(code)
            elif event == xlib.X.ButtonRelease:
                display_instance.button_release_attempts += 1
                if display_instance.drop_next_button_release:
                    display_instance.drop_next_button_release = False
                else:
                    display_instance.buttons_down.discard(code)

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
            pointer_lease = Lease()
            pointer_lease.expected_surface = 52
            pointer_lease.expected_geometry = [0, 0, 100, 100]
            owner.call("button_down", pointer_lease, 1)
            owner.call("button_up", pointer_lease, 1)
            self.assertEqual(display_instance.buttons_down, {1})

            pointer_result = owner.call("release", pointer_lease)

            self.assertTrue(pointer_result["verified"])
            self.assertEqual(pointer_result["buttons_down"], [])
            self.assertEqual(display_instance.buttons_down, set())
            self.assertEqual(display_instance.button_release_attempts, 2)

            successful_pointer_lease = Lease()
            successful_pointer_lease.expected_surface = 52
            successful_pointer_lease.expected_geometry = [0, 0, 100, 100]
            owner.call("button_down", successful_pointer_lease, 1)
            owner.call("button_up", successful_pointer_lease, 1)
            self.assertEqual(display_instance.buttons_down, set())
            owner.call("release", successful_pointer_lease)
            self.assertEqual(display_instance.button_release_attempts, 3)
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
