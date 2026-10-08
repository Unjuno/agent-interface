"""Wheel cleanup bookkeeping against a synthetic X server, without OS input.

This does not establish ownership of globally sampled X11 button state.
"""
import importlib.util
import sys
import types
import unittest
from collections import Counter
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch

LIVE = Path(__file__).resolve().parent
sys.path.insert(0, str(LIVE))

from test_input_owner_v12_cleanup_after_explicit_up import FakeDisplay, Lease


@contextmanager
def wheel_owner(faults=None):
    """Fault keys are (event type, attempt number); values describe delivery."""
    server = FakeDisplay()
    events = []
    attempts = Counter()
    faults = {} if faults is None else faults
    xlib = types.ModuleType("Xlib")
    xlib.X = types.SimpleNamespace(
        KeyPress=2, KeyRelease=3, ButtonPress=4, ButtonRelease=5,
        Button1Mask=256, AnyPropertyType=0, IsViewable=2)
    xlib.XK = types.ModuleType("Xlib.XK")
    xlib.XK.string_to_keysym = lambda _key: 1
    xlib.display = types.ModuleType("Xlib.display")
    xlib.display.Display = lambda _name: server
    xlib.error = types.ModuleType("Xlib.error")
    xlib.error.BadWindow = type("BadWindow", (Exception,), {})
    xlib.error.BadDrawable = type("BadDrawable", (Exception,), {})
    xlib.ext = types.ModuleType("Xlib.ext")
    xtest = types.ModuleType("Xlib.ext.xtest")
    xlib.ext.xtest = xtest

    def fake_input(display, event, button):
        if display is not server or event not in (4, 5) or button not in (4, 5):
            raise AssertionError("unexpected XTest wheel request")
        events.append((event, button))
        attempts[event] += 1
        mode = faults.get((event, attempts[event]))
        if mode == "raise_before":
            raise RuntimeError("injected delivery failure")
        if mode == "drop":
            return
        if event == 4:
            server.buttons_down.add(button)
        else:
            server.buttons_down.discard(button)
        if mode == "raise_after":
            raise RuntimeError("injected delivery failure")

    xtest.fake_input = fake_input
    exceptions = types.ModuleType("executor_v3")
    exceptions.Cancelled = type("Cancelled", (Exception,), {})
    exceptions.DecisionRequired = type("DecisionRequired", (Exception,), {})
    modules = {"Xlib": xlib, "Xlib.X": xlib.X, "Xlib.XK": xlib.XK,
               "Xlib.display": xlib.display, "Xlib.error": xlib.error,
               "Xlib.ext": xlib.ext, "Xlib.ext.xtest": xtest,
               "executor_v3": exceptions}
    with patch.dict(sys.modules, modules):
        spec = importlib.util.spec_from_file_location(
            "wheel_cleanup_owner", Path(__file__).with_name("input_owner_v12.py"))
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        owner = module.InputOwner(":fake")
        lease = Lease()
        lease.expected_surface = 52
        lease.expected_geometry = [0, 0, 100, 100]
        try:
            yield owner, lease, server, events
        finally:
            # Finish the real owner thread before removing its fake dependencies.
            owner.close()


class WheelCleanupTests(unittest.TestCase):
    def assert_released(self, owner, lease, server):
        result = owner.call("release", lease)
        self.assertEqual(server.buttons_down, set())
        self.assertEqual(result["buttons_down"], [])
        self.assertTrue(result["verified"])

    def test_successful_notches_do_not_get_duplicate_terminal_up(self):
        for count, button in ((1, 4), (-1, 5), (3, 4), (-3, 5)):
            with self.subTest(count=count), wheel_owner() as fixture:
                owner, lease, server, events = fixture
                result = owner.call("wheel", lease, count)
                self.assertEqual(result["payload"], count)
                self.assert_released(owner, lease, server)
                self.assertEqual(events, [(4, button), (5, button)] * abs(count))

    def test_dropped_final_up_is_retried_for_each_wheel_direction(self):
        for count, button in ((1, 4), (-1, 5), (3, 4), (-3, 5)):
            with self.subTest(count=count), wheel_owner(
                    {(5, abs(count)): "drop"}) as fixture:
                owner, lease, server, events = fixture
                owner.call("wheel", lease, count)
                self.assertEqual(server.buttons_down, {button})
                self.assert_released(owner, lease, server)
                self.assertEqual(events,
                                 [(4, button), (5, button)] * abs(count) + [(5, button)])

    def test_press_delivered_before_exception_remains_releasable(self):
        for count, button in ((1, 4), (-1, 5)):
            with self.subTest(count=count), wheel_owner({(4, 1): "raise_after"}) as fixture:
                owner, lease, server, events = fixture
                with self.assertRaisesRegex(RuntimeError, "injected delivery failure"):
                    owner.call("wheel", lease, count)
                self.assertEqual(server.buttons_down, {button})
                self.assert_released(owner, lease, server)
                self.assertEqual(events, [(4, button), (5, button)])

    def test_exception_before_up_delivery_remains_releasable(self):
        for count, button in ((1, 4), (-1, 5)):
            with self.subTest(count=count), wheel_owner({(5, 1): "raise_before"}) as fixture:
                owner, lease, server, events = fixture
                with self.assertRaisesRegex(RuntimeError, "injected delivery failure"):
                    owner.call("wheel", lease, count)
                self.assertEqual(server.buttons_down, {button})
                self.assert_released(owner, lease, server)
                self.assertEqual(events, [(4, button), (5, button), (5, button)])

    def test_exception_after_up_delivery_does_not_cause_duplicate_up(self):
        for count, button in ((1, 4), (-1, 5)):
            with self.subTest(count=count), wheel_owner({(5, 1): "raise_after"}) as fixture:
                owner, lease, server, events = fixture
                with self.assertRaisesRegex(RuntimeError, "injected delivery failure"):
                    owner.call("wheel", lease, count)
                self.assert_released(owner, lease, server)
                self.assertEqual(events, [(4, button), (5, button)])

    def test_close_retries_dropped_up_without_explicit_release(self):
        for count, button in ((1, 4), (-1, 5)):
            with self.subTest(count=count), wheel_owner({(5, 1): "drop"}) as fixture:
                owner, lease, server, events = fixture
                owner.call("wheel", lease, count)
                owner.close()
                self.assertTrue(owner.stopped.is_set())
                self.assertEqual(server.buttons_down, set())
                self.assertTrue(owner.records[-1]["verified"])
                self.assertEqual(events, [(4, button), (5, button), (5, button)])

    def test_failed_cleanup_reports_unverified_and_retains_retry(self):
        for count, button in ((1, 4), (-1, 5)):
            with self.subTest(count=count), wheel_owner(
                    {(5, 1): "drop", (5, 2): "drop"}) as fixture:
                owner, lease, server, events = fixture
                owner.call("wheel", lease, count)
                with self.assertRaisesRegex(RuntimeError, "owner release not verified"):
                    owner.call("release", lease)
                self.assertFalse(owner.records[-1]["verified"])
                self.assertEqual(owner.records[-1]["buttons_down"], [button])
                self.assertEqual(server.buttons_down, {button})
                self.assert_released(owner, lease, server)
                self.assertEqual(events, [(4, button), (5, button), (5, button), (5, button)])


if __name__ == "__main__":
    unittest.main(verbosity=2)
