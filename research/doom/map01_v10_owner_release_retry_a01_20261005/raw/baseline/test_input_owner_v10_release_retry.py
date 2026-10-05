"""Regression tests for X11 key/button releases omitted by the server."""
import sys
import threading
import types
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))


class Display:
    def __init__(self):
        self.keys = set()
        self.buttons = set()
        self.drop_key_release = False
        self.drop_button_release = False
        self.suppress_key_releases = False
        self.root = Root(self)

    def get_input_focus(self):
        return types.SimpleNamespace(focus=41)

    def keysym_to_keycode(self, _symbol):
        return 65

    def query_keymap(self):
        bitmap = bytearray(32)
        for code in self.keys:
            bitmap[code // 8] |= 1 << (code % 8)
        return bytes(bitmap)

    def screen(self):
        return types.SimpleNamespace(root=self.root)

    def create_resource_object(self, _kind, identifier):
        return Window(self, identifier, parent=Window(self, 52) if identifier == 41 else None)

    def intern_atom(self, _name):
        return 1

    def sync(self):
        pass

    def close(self):
        pass


class Window:
    def __init__(self, display, identifier, parent=None):
        self.display, self.id, self.parent = display, identifier, parent

    def get_geometry(self):
        return types.SimpleNamespace(width=100, height=100)

    def get_attributes(self):
        return types.SimpleNamespace(map_state=2)

    def query_tree(self):
        return types.SimpleNamespace(parent=self.parent)


class Root:
    id = 1

    def __init__(self, display):
        self.display = display

    def query_pointer(self):
        mask = sum(256 << (button - 1) for button in self.display.buttons)
        return types.SimpleNamespace(mask=mask, root_x=5, root_y=5)

    def get_full_property(self, _atom, _kind):
        return types.SimpleNamespace(value=[52])

    def translate_coords(self, source, x, y):
        if isinstance(source, Root):
            return types.SimpleNamespace(child=Window(self.display, 52), x=x, y=y)
        return types.SimpleNamespace(child=None, x=0, y=0)

    def get_geometry(self):
        return types.SimpleNamespace(width=100, height=100)


class Lease:
    def __init__(self):
        self.deadline = 2**62
        self.cancel = threading.Event()
        self.expected_focus = 41
        self.expected_surface = 52
        self.expected_geometry = [0, 0, 100, 100]
        self.focus_invalid = False

    def check(self):
        pass


class InputOwnerV10ReleaseRetryTests(unittest.TestCase):
    def setUp(self):
        self.display = Display()
        self.saved = {name: sys.modules.get(name) for name in (
            "Xlib", "Xlib.X", "Xlib.XK", "Xlib.display", "Xlib.error",
            "Xlib.ext", "Xlib.ext.xtest", "executor_v3", "input_owner_v10")}
        x = types.SimpleNamespace(KeyPress=2, KeyRelease=3, ButtonPress=4,
                                  ButtonRelease=5, Button1Mask=256,
                                  AnyPropertyType=0, IsViewable=2)
        xlib = types.ModuleType("Xlib")
        xlib.X = x
        xk = types.ModuleType("Xlib.XK")
        xk.string_to_keysym = lambda _value: 1
        display_module = types.ModuleType("Xlib.display")
        display_module.Display = lambda _name: self.display
        error = types.ModuleType("Xlib.error")
        error.BadWindow = type("BadWindow", (Exception,), {})
        error.BadDrawable = type("BadDrawable", (Exception,), {})
        ext = types.ModuleType("Xlib.ext")
        xtest = types.ModuleType("Xlib.ext.xtest")

        def fake_input(_display, event, value, **_kwargs):
            if event == x.KeyPress:
                self.display.keys.add(value)
            elif event == x.KeyRelease:
                if self.display.drop_key_release or self.display.suppress_key_releases:
                    self.display.drop_key_release = False
                else:
                    self.display.keys.discard(value)
            elif event == x.ButtonPress:
                self.display.buttons.add(value)
            elif event == x.ButtonRelease:
                if self.display.drop_button_release:
                    self.display.drop_button_release = False
                else:
                    self.display.buttons.discard(value)

        xtest.fake_input = fake_input
        ext.xtest = xtest
        xlib.XK, xlib.display, xlib.error, xlib.ext = xk, display_module, error, ext
        executor = types.ModuleType("executor_v3")
        executor.Cancelled = type("Cancelled", (Exception,), {})
        executor.DecisionRequired = type("DecisionRequired", (Exception,), {})
        sys.modules.update({"Xlib": xlib, "Xlib.X": types.ModuleType("Xlib.X"),
            "Xlib.XK": xk, "Xlib.display": display_module, "Xlib.error": error,
            "Xlib.ext": ext, "Xlib.ext.xtest": xtest, "executor_v3": executor})
        sys.modules.pop("input_owner_v10", None)
        from input_owner_v10 import InputOwner
        self.owner = InputOwner(":fake")

    def tearDown(self):
        try:
            self.display.keys.clear()
            self.display.buttons.clear()
            self.owner.close()
        finally:
            for name, module in self.saved.items():
                if module is None:
                    sys.modules.pop(name, None)
                else:
                    sys.modules[name] = module

    def test_cleanup_retries_a_key_still_down_after_explicit_up(self):
        lease = Lease()
        self.owner.call("down", lease, "A")
        self.display.drop_key_release = True
        self.owner.call("up", lease, "A")
        self.assertEqual(self.display.keys, {65})

        receipt = self.owner.call("release", lease)

        self.assertTrue(receipt["verified"])
        self.assertEqual(receipt["keys_down"], [])
        self.assertEqual(self.display.keys, set())

    def test_cleanup_retries_a_wheel_release_omitted_by_server(self):
        lease = Lease()
        self.display.drop_button_release = True
        self.owner.call("wheel", lease, 1)
        self.assertEqual(self.display.buttons, {4})

        receipt = self.owner.call("release", lease)

        self.assertTrue(receipt["verified"])
        self.assertEqual(receipt["buttons_down"], [])
        self.assertEqual(self.display.buttons, set())

    def test_persistent_key_release_failure_remains_unverified(self):
        lease = Lease()
        self.owner.call("down", lease, "A")
        self.display.suppress_key_releases = True

        with self.assertRaisesRegex(RuntimeError, "owner release not verified"):
            self.owner.call("release", lease)

        receipt = [row for row in self.owner.records if row.get("event") == "owner_release"][-1]
        self.assertFalse(receipt["verified"])
        self.assertEqual(receipt["keys_down"], [65])
        self.assertEqual(self.display.keys, {65})


if __name__ == "__main__":
    unittest.main()
