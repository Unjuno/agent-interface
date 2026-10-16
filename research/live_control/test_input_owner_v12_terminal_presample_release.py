"""Terminal cleanup still sends bounded key-up when its first sample fails."""
import sys
import types
import unittest

from test_input_owner_v12_explicit_up_cancel import FakeDisplay, Lease


class TerminalPreSampleReleaseTests(unittest.TestCase):
    def test_terminal_cleanup_sends_up_and_retains_unknown_sample_state(self):
        names = ("Xlib", "Xlib.X", "Xlib.XK", "Xlib.display", "Xlib.error",
                 "Xlib.ext", "Xlib.ext.xtest")
        saved = {name: sys.modules.get(name) for name in names}
        display_instance = FakeDisplay()
        xlib = types.ModuleType("Xlib")
        xlib.X = types.SimpleNamespace(KeyPress=2, KeyRelease=3, ButtonRelease=5,
                                       Button1Mask=256, AnyPropertyType=0)
        xk = types.ModuleType("Xlib.XK")
        xk.string_to_keysym = lambda key: ord(key)
        display = types.ModuleType("Xlib.display")
        display.Display = lambda _name: display_instance
        error = types.ModuleType("Xlib.error")
        error.BadWindow = type("BadWindow", (Exception,), {})
        error.BadDrawable = type("BadDrawable", (Exception,), {})
        ext = types.ModuleType("Xlib.ext")
        xtest = types.ModuleType("Xlib.ext.xtest")

        def fake_input(_display, event, code):
            display_instance.trace.append(("key_event", event, code))
            if event == xlib.X.KeyPress:
                display_instance.down.add(code)
            elif event == xlib.X.KeyRelease:
                display_instance.keyrelease_attempts += 1
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
            for name in ("input_owner_v12", "input_transition_owner_v3",
                         "input_transition_owner_v4"):
                sys.modules.pop(name, None)
            from input_transition_owner_v4 import InputOwner

            owner = InputOwner(":fake")
            lease = Lease()
            owner.call("down", lease, "W")
            display_instance.fail_keymap_queries = 100

            result = owner.call("release", lease)

            receipt = next(row for row in reversed(owner.records)
                           if row.get("event") == "owner_release")
            self.assertEqual(display_instance.keyrelease_attempts, 3)
            self.assertFalse(receipt["verified"])
            self.assertEqual(receipt["keys_unknown"], [38])
            self.assertEqual(len(receipt["key_release_attempts"]["38"]["attempts"]), 3)
            self.assertEqual(
                receipt["key_release_attempts"]["38"]["attempts"][0]
                ["keymap_before_error"]["type"], "RuntimeError")
            self.assertFalse(result["verified"])
        finally:
            if owner is not None:
                display_instance.fail_keymap_queries = 0
                owner.close()
            for name in ("input_transition_owner_v4", "input_transition_owner_v3",
                         "input_owner_v12"):
                sys.modules.pop(name, None)
            for name, module in saved.items():
                if module is None:
                    sys.modules.pop(name, None)
                else:
                    sys.modules[name] = module


if __name__ == "__main__":
    unittest.main()
