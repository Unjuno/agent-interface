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
        self.drop_keyreleases = 0
        self.keyrelease_attempts = 0
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
        self.intent_token = "test-intent"
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
                display_instance.keyrelease_attempts += 1
                if display_instance.drop_keyreleases:
                    display_instance.drop_keyreleases -= 1
                else:
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

    def test_lost_explicit_keyup_is_retried_and_receipt_uses_server_keymap(self):
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
            if event == xlib.X.KeyPress:
                display_instance.down.add(code)
            elif event == xlib.X.KeyRelease:
                display_instance.keyrelease_attempts += 1
                if display_instance.drop_keyreleases:
                    display_instance.drop_keyreleases -= 1
                else:
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
            display_instance.drop_keyreleases = 1
            row = owner.call("up", lease, "W")

            receipt = row["owner_thread_keyup_receipt"]
            self.assertTrue(row["owner_thread_keyup_verified"], row)
            self.assertTrue(receipt["server_keyup_verified"])
            self.assertEqual(receipt["server_keyup_attempt_count"], 2)
            self.assertEqual(display_instance.keyrelease_attempts, 2)
            self.assertEqual(display_instance.down, set())

            owner.call("down", lease, "W")
            display_instance.drop_keyreleases = 1
            release = owner.call("release", lease)
            self.assertTrue(release["verified"])
            self.assertEqual(release["keys_down"], [])
            self.assertEqual(len(release["key_release_attempts"]["38"]["attempts"]), 2)
            self.assertEqual(release["key_release_intervals_ns"][0]["keycode"], 38)

            owner.call("down", lease, "W")
            display_instance.drop_keyreleases = 3
            failed_transition = owner.call("up", lease, "W")
            failed_receipt = owner.records[-1]
            self.assertFalse(failed_transition["owner_thread_keyup_verified"])
            self.assertEqual(failed_transition["owner_thread_keyup_receipt_count"], 1)
            self.assertEqual(failed_transition["owner_thread_keyup_receipt"], failed_receipt)
            self.assertFalse(failed_receipt["server_keyup_verified"])
            self.assertEqual(failed_receipt["server_keyup_attempt_count"], 3)
            self.assertEqual(display_instance.down, {38})
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

    def test_persistent_keyup_loss_preserves_v15_batch_and_v13_terminal_receipts(self):
        from executor_v13 import Executor
        from lease_release_v1 import Lease as InputLease
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
            if event == xlib.X.KeyPress:
                display_instance.down.add(code)
            elif event == xlib.X.KeyRelease:
                display_instance.keyrelease_attempts += 1
                if display_instance.drop_keyreleases:
                    display_instance.drop_keyreleases -= 1
                else:
                    display_instance.down.discard(code)

        xtest.fake_input = fake_input
        ext.xtest = xtest
        xlib.XK, xlib.display, xlib.error, xlib.ext = xk, display, error, ext
        sys.modules.update({"Xlib": xlib, "Xlib.X": types.ModuleType("Xlib.X"),
                            "Xlib.XK": xk, "Xlib.display": display,
                            "Xlib.error": error, "Xlib.ext": ext,
                            "Xlib.ext.xtest": xtest})
        doom = LIVE.parent / "doom"
        sys.path.insert(0, str(doom))
        composed_names = ("doom_typed_release_backend_v1",
                          "doom_typed_release_backend_v2",
                          "doom_owner_thread_release_batch_backend_v1")
        saved_composed = {name: sys.modules.get(name) for name in composed_names}
        owner = None
        try:
            for name in ("input_owner_v12", "input_transition_owner_v3",
                         "input_transition_owner_v4", *composed_names):
                sys.modules.pop(name, None)
            from input_transition_owner_v4 import InputOwner

            # Supply only the base key-step engine; exercise the real V15
            # release-batch adapter, V4/V3/V12 owner chain and V13 cleanup.
            class FakeBaseBackend:
                def execute(self, _step, _lease, _identifier, _index):
                    self.raw("W", True)
                    self.raw("W", False)

                def release_all(self):
                    return self.owner.call("release", self.lease)

            release_v1 = types.ModuleType("doom_typed_release_backend_v1")
            release_v1.Backend = FakeBaseBackend
            release_v1.suite = lambda: None
            sys.modules["doom_typed_release_backend_v1"] = release_v1
            from doom_owner_thread_release_batch_backend_v1 import Backend as V15Backend

            owner = InputOwner(":fake")
            lease = InputLease(__import__("time").perf_counter_ns() + 10_000_000_000)
            lease.expected_focus = 41
            lease.focus_invalid = False
            display_instance.drop_keyreleases = 6
            backend = object.__new__(V15Backend)
            backend.owner = owner
            backend.held = set()
            backend.lease = lease
            backend.emit = lambda event: events.append(event)
            backend._input_event_context = None
            backend._release_batch = threading.local()
            backend._last_release_batch_delivery = None
            events = []
            executor = Executor(backend, events.append)
            executor.active = ("persistent-loss", lease, threading.current_thread())
            executor.release_watch_stops["persistent-loss"] = threading.Event()
            executor._run_with_watcher_cleanup(
                "persistent-loss", [{"op": "fake-key-up"}], lease)

            terminal = next(row for row in events if row.get("event") == "terminal")
            batch_row = next(row for row in events
                             if row.get("release_batch_schema") == "input-release-batch-v3")
            explicit = next(row for row in owner.records
                            if row.get("event") == "owner_explicit_keyup")
            cleanup = next(row for row in owner.records
                           if row.get("event") == "owner_release")
            self.assertEqual(terminal["status"], "failed")
            self.assertFalse(terminal["release"]["verified"])
            self.assertEqual(terminal["release"]["keys_down"], [38])
            self.assertEqual(len(terminal["release"]["key_release_attempts"]["38"]["attempts"]), 3)
            self.assertTrue(batch_row["release_batch_complete"])
            self.assertFalse(batch_row["owner_transition_verified"])
            self.assertFalse(batch_row["owner_thread_keyup_verified"])
            self.assertEqual(batch_row["owner_thread_keyup_receipt"], explicit)
            self.assertEqual(batch_row["owned_keycodes_after_batch"], [38])
            self.assertEqual(explicit["server_keyup_attempt_count"], 3)
            self.assertFalse(explicit["server_keyup_verified"])
            self.assertEqual(cleanup["key_release_attempts"]["38"]["attempts"][0]["attempt"], 1)
            self.assertEqual(len(cleanup["key_release_attempts"]["38"]["attempts"]), 3)
            self.assertFalse(cleanup["verified"])
            self.assertEqual(cleanup["keys_down"], [38])
            self.assertEqual(display_instance.keyrelease_attempts, 6)
            self.assertEqual(display_instance.down, {38})
        finally:
            if owner is not None:
                owner.close()
            for name in ("input_transition_owner_v4", "input_transition_owner_v3",
                         "input_owner_v12", *composed_names):
                sys.modules.pop(name, None)
            for name, module in saved_composed.items():
                if module is not None:
                    sys.modules[name] = module
            try:
                sys.path.remove(str(doom))
            except ValueError:
                pass
            for name, module in saved.items():
                if module is None:
                    sys.modules.pop(name, None)
                else:
                    sys.modules[name] = module


if __name__ == "__main__":
    unittest.main(verbosity=2)
