"""Cancellation arriving inside explicit key-up XSync must not look ordinary."""
import sys
import threading
import types
import unittest
import json
import os
from pathlib import Path

LIVE = Path(__file__).resolve().parent
sys.path.insert(0, str(LIVE))

# Load executor exception types before replacing Xlib with this test's fake server.
import executor_v3


class FakeDisplay:
    def __init__(self):
        self.down = set()
        self.on_sync = None
        self.fail_keymap_queries = 0
        self.keymap_queries = 0
        self.key_events = []
        self.trace = []
        self.root = types.SimpleNamespace(
            query_pointer=lambda: types.SimpleNamespace(mask=0, root_x=0, root_y=0))

    def get_input_focus(self):
        return types.SimpleNamespace(focus=41)

    def keysym_to_keycode(self, _keysym):
        return 38

    def screen(self):
        return types.SimpleNamespace(root=self.root)

    def query_keymap(self):
        self.keymap_queries += 1
        if self.fail_keymap_queries:
            self.fail_keymap_queries -= 1
            self.trace.append(["query_keymap", "raise", sorted(self.down)])
            raise RuntimeError("synthetic keymap sample failure")
        self.trace.append(["query_keymap", "return", sorted(self.down)])
        bitmap = bytearray(32)
        for code in self.down:
            bitmap[code // 8] |= 1 << (code % 8)
        return bytes(bitmap)

    def sync(self):
        self.trace.append(["sync"])
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
    def test_keyrelease_send_failure_retains_receipt_and_retries(self):
        names = ("Xlib", "Xlib.X", "Xlib.XK", "Xlib.display", "Xlib.error",
                 "Xlib.ext", "Xlib.ext.xtest")
        saved = {name: sys.modules.get(name) for name in names}
        display_instance = FakeDisplay()
        display_instance.keysym_to_keycode = lambda keysym: {87: 38, 83: 39}[keysym]
        xlib = types.ModuleType("Xlib")
        xlib.X = types.SimpleNamespace(KeyPress=2, KeyRelease=3, ButtonRelease=5,
                                       Button1Mask=256, AnyPropertyType=0)
        xk = types.ModuleType("Xlib.XK")
        xk.string_to_keysym = lambda key: {"W": 87, "S": 83}[key]
        display = types.ModuleType("Xlib.display")
        display.Display = lambda _name: display_instance
        error = types.ModuleType("Xlib.error")
        error.BadWindow = type("BadWindow", (Exception,), {})
        error.BadDrawable = type("BadDrawable", (Exception,), {})
        ext = types.ModuleType("Xlib.ext")
        xtest = types.ModuleType("Xlib.ext.xtest")
        failed_codes = {38}

        def fake_input(_display, event, code):
            display_instance.key_events.append((event, code))
            display_instance.trace.append(["key_event", event, code])
            if event == xlib.X.KeyPress:
                display_instance.down.add(code)
            elif event == xlib.X.KeyRelease:
                if code in failed_codes:
                    failed_codes.remove(code)
                    display_instance.trace.append(["key_event", "raise", code])
                    raise RuntimeError("synthetic KeyRelease send failure")
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
            owner.call("down", lease, "S")
            with self.assertRaises(RuntimeError) as raised:
                owner.call("release", lease)

            receipt = getattr(raised.exception, "owner_release_record", None)
            self.assertIsInstance(receipt, dict)
            self.assertEqual(receipt["event"], "owner_release")
            self.assertFalse(receipt["verified"])
            self.assertEqual(receipt["keys_down"], [38])
            self.assertEqual(receipt["keys_unknown"], [])
            self.assertEqual(receipt["key_state_errors"], [])
            self.assertEqual(receipt["release_errors"][0]["source"], "key_release")
            self.assertEqual(receipt["release_errors"][0]["keycode"], 38)
            self.assertEqual(receipt["release_errors"][0]["type"], "RuntimeError")
            self.assertEqual(display_instance.keymap_queries, 1)
            self.assertEqual(display_instance.down, {38})
            self.assertEqual(display_instance.key_events[-2:], [(xlib.X.KeyRelease, 38),
                                                                (xlib.X.KeyRelease, 39)])

            recovered = owner.call("release", lease)
            self.assertTrue(recovered["verified"])
            self.assertEqual(recovered["keys_down"], [])
            self.assertEqual(recovered["keys_unknown"], [])
            self.assertEqual(display_instance.down, set())
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

    def test_cancel_during_keyup_sync_is_not_marked_ordinary(self):
        names = ("Xlib", "Xlib.X", "Xlib.XK", "Xlib.display", "Xlib.error",
                 "Xlib.ext", "Xlib.ext.xtest")
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
            display_instance.key_events.append((event, code))
            display_instance.trace.append(["key_event", event, code])
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
            for name in ("input_transition_owner_v4", "input_transition_owner_v3",
                         "input_owner_v12"):
                sys.modules.pop(name, None)
            for name, module in saved.items():
                if module is None:
                    sys.modules.pop(name, None)
                else:
                    sys.modules[name] = module

    def test_terminal_cleanup_sample_failure_retains_unverified_receipt_and_retries(self):
        names = ("Xlib", "Xlib.X", "Xlib.XK", "Xlib.display", "Xlib.error",
                 "Xlib.ext", "Xlib.ext.xtest")
        saved = {name: sys.modules.get(name) for name in names}
        display_instance = FakeDisplay()
        xlib = types.ModuleType("Xlib")
        xlib.X = types.SimpleNamespace(KeyPress=2, KeyRelease=3, ButtonRelease=5,
                                       Button1Mask=256, AnyPropertyType=0)
        xk = types.ModuleType("Xlib.XK")
        xk.string_to_keysym = lambda _key: 1
        display = types.ModuleType("Xlib.display")
        display.Display = lambda _name: display_instance
        error_module = types.ModuleType("Xlib.error")
        error_module.BadWindow = type("BadWindow", (Exception,), {})
        error_module.BadDrawable = type("BadDrawable", (Exception,), {})
        ext = types.ModuleType("Xlib.ext")
        xtest = types.ModuleType("Xlib.ext.xtest")

        def fake_input(_display, event, code):
            display_instance.key_events.append((event, code))
            display_instance.trace.append(["key_event", event, code])
            if event == xlib.X.KeyPress:
                display_instance.down.add(code)
            elif event == xlib.X.KeyRelease:
                display_instance.down.discard(code)

        xtest.fake_input = fake_input
        ext.xtest = xtest
        xlib.XK, xlib.display, xlib.error, xlib.ext = xk, display, error_module, ext
        sys.modules.update({"Xlib": xlib, "Xlib.X": types.ModuleType("Xlib.X"),
                            "Xlib.XK": xk, "Xlib.display": display,
                            "Xlib.error": error_module, "Xlib.ext": ext,
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
            display_instance.fail_keymap_queries = 1

            with self.assertRaisesRegex(RuntimeError, "owner release not verified") as raised:
                owner.call("release", lease)

            receipt = getattr(raised.exception, "owner_release_record", None)
            self.assertIsInstance(receipt, dict)
            self.assertEqual(receipt["event"], "owner_release")
            self.assertFalse(receipt["verified"])
            self.assertEqual(receipt["keys_unknown"], [38])
            self.assertEqual(receipt["keys_down"], [])
            self.assertTrue(receipt["key_state_errors"])
            self.assertIn((xlib.X.KeyRelease, 38), display_instance.key_events)
            self.assertEqual(display_instance.down, set())
            self.assertIn(receipt, owner._inner.records)
            server_keys_after_failed_sample = sorted(display_instance.down)

            recovered = owner.call("release", lease)
            self.assertTrue(recovered["verified"])
            self.assertEqual(recovered["keys_down"], [])
            self.assertEqual(recovered["keys_unknown"], [])
            self.assertEqual(display_instance.down, set())
            output_dir = os.environ.get("AI_RESEARCH_OUT")
            if output_dir:
                raw = {
                    "schema": "v39-terminal-release-sample-error-raw-v1",
                    "test": "test_terminal_cleanup_sample_failure_retains_unverified_receipt_and_retries",
                    "keycode": 38,
                    "key_events": display_instance.key_events,
                    "trace": display_instance.trace,
                    "keymap_query_attempts": display_instance.keymap_queries,
                    "failed_release_receipt": receipt,
                    "recovery_release_receipt": recovered,
                    "server_keys_after_failed_sample": server_keys_after_failed_sample,
                    "server_keys_after_recovery": sorted(display_instance.down),
                    "raised_error": {
                        "type": type(raised.exception).__name__,
                        "message": str(raised.exception),
                        "has_owner_release_record": getattr(
                            raised.exception, "owner_release_record", None) is receipt,
                    },
                }
                Path(output_dir, "cleanup-sample-failure.raw.json").write_text(
                    json.dumps(raw, sort_keys=True, indent=2) + "\n", encoding="utf-8")
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
