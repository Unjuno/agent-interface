"""An admitted key remains releasable after its keysym mapping disappears."""
import importlib.util
import os
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
        self.keymap = {}
        self.root = types.SimpleNamespace(
            query_pointer=lambda: types.SimpleNamespace(mask=0))

    def get_input_focus(self):
        return types.SimpleNamespace(focus=41)

    def keysym_to_keycode(self, keysym):
        return self.keymap.get(keysym, keysym)

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

    def check(self):
        pass


class KeyUpAfterKeysymRemovalTests(unittest.TestCase):
    def test_up_uses_admitted_code_when_current_keysym_has_no_code(self):
        xlib_names = ("Xlib", "Xlib.X", "Xlib.XK", "Xlib.display", "Xlib.error",
                      "Xlib.ext", "Xlib.ext.xtest")
        owner_names = ("input_owner_v12", "input_transition_owner_v3",
                       "input_transition_owner_v4")
        saved = {name: sys.modules.get(name) for name in xlib_names + owner_names}
        display_instance = FakeDisplay()
        x = types.SimpleNamespace(KeyPress=2, KeyRelease=3, ButtonRelease=5,
                                  Button1Mask=256, AnyPropertyType=0)
        xlib = types.ModuleType("Xlib")
        xlib.X = x
        xk = types.ModuleType("Xlib.XK")
        xk.string_to_keysym = lambda key: ord(key[0])
        display = types.ModuleType("Xlib.display")
        display.Display = lambda _name: display_instance
        error = types.ModuleType("Xlib.error")
        error.BadWindow = type("BadWindow", (Exception,), {})
        error.BadDrawable = type("BadDrawable", (Exception,), {})
        ext = types.ModuleType("Xlib.ext")
        xtest = types.ModuleType("Xlib.ext.xtest")

        def fake_input(_display, event, code):
            if event == x.KeyPress:
                display_instance.down.add(code)
            elif event == x.KeyRelease:
                display_instance.down.discard(code)

        xtest.fake_input = fake_input
        ext.xtest = xtest
        xlib.XK, xlib.display, xlib.error, xlib.ext = xk, display, error, ext
        sys.modules.update({
            "Xlib": xlib, "Xlib.X": types.ModuleType("Xlib.X"), "Xlib.XK": xk,
            "Xlib.display": display, "Xlib.error": error, "Xlib.ext": ext,
            "Xlib.ext.xtest": xtest,
        })
        owner = None
        try:
            for name in owner_names:
                sys.modules.pop(name, None)
            owner_source = Path(os.environ.get(
                "INPUT_OWNER_V12_SOURCE", LIVE / "input_owner_v12.py"))
            spec = importlib.util.spec_from_file_location(
                "input_owner_v12", owner_source)
            owner_module = importlib.util.module_from_spec(spec)
            sys.modules["input_owner_v12"] = owner_module
            spec.loader.exec_module(owner_module)
            owner = owner_module.InputOwner(":fake")
            lease = Lease()

            admission = owner.call("down", lease, "W")
            self.assertEqual(admission["keycode"], 87)
            self.assertEqual(display_instance.down, {87})
            display_instance.keymap[ord("W")] = 0

            error_after_up = None
            try:
                owner.call("up", lease, "W")
            except Exception as exc:
                error_after_up = repr(exc)
            observation = {
                "error_after_up": error_after_up,
                "keys_down": sorted(display_instance.down),
                "keyups": [row for row in owner.records
                           if row.get("event") == "owner_explicit_keyup"],
            }
            self.assertIsNone(error_after_up, observation)
            self.assertEqual(observation["keys_down"], [])
            self.assertEqual(len(observation["keyups"]), 1)
            self.assertEqual(observation["keyups"][0]["key"], "W")
            self.assertEqual(observation["keyups"][0]["keycode"], 87)
        finally:
            if owner is not None:
                owner.close()
            for name, module in saved.items():
                if module is None:
                    sys.modules.pop(name, None)
                else:
                    sys.modules[name] = module


if __name__ == "__main__":
    unittest.main(verbosity=2)
