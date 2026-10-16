"""Reproduce a cancellation cleanup racing a delayed batched key-up."""
import sys
import threading
import types
import unittest
from pathlib import Path

LIVE = Path(__file__).resolve().parent
sys.path.insert(0, str(LIVE))

from test_input_owner_v12_explicit_up_cancel import FakeDisplay, Lease


class CancelledUpBatchTests(unittest.TestCase):
    def test_verified_cancel_cleanup_is_joined_to_delayed_batch(self):
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
            for name in ("input_owner_v12", "input_transition_owner_v3",
                         "input_transition_owner_v4"):
                sys.modules.pop(name, None)
            from input_transition_owner_v4 import InputOwner

            owner = InputOwner(":fake")
            lease = Lease()
            owner.call("down", lease, "W")
            lease.cancel.set()
            self.assertTrue(lease.interrupted.wait(1), "owner did not process cancellation")
            cleanup = lease.interruptions[-1]
            self.assertEqual(cleanup["reason"], "cancelled")
            self.assertTrue(cleanup["verified"])
            self.assertEqual(display_instance.down, set())

            # The backend already queued this UP before cancellation cleanup
            # won the owner thread. It must not be mistaken for a fresh UP.
            rows = owner.call("up_batch", lease, ["W"])
            self.assertEqual(len(rows), 1)
            self.assertFalse(rows[0]["owner_thread_keyup_verified"])
            self.assertFalse(rows[0]["ordinary_release_candidate"])
            self.assertFalse(rows[0]["grants_input_authority"])
            self.assertEqual(display_instance.down, set())

            # A different lease cannot borrow the prior lease's cleanup.
            wrong_lease = Lease()
            with self.assertRaises(ValueError):
                owner.call("up_batch", wrong_lease, ["W"])

            second_lease = Lease()
            owner.call("down", second_lease, "W")
            second_lease.cancel.set()
            self.assertTrue(second_lease.interrupted.wait(1))
            # A cleanup record without a verified key-up sample must remain
            # a hard failure, even when the lease and key identity match.
            owner._inner.records[-1]["key_release_attempts"]["38"]["verified"] = False
            with self.assertRaisesRegex(ValueError, "active input lease"):
                owner.call("up_batch", second_lease, ["W"])
        finally:
            if owner is not None:
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
    unittest.main(verbosity=2)
