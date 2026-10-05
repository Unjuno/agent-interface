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
        self.trace = []
        self.on_sync = None
        self.fail_keymap_queries = 0
        self.fail_keyrelease_syncs = 0
        self.root = types.SimpleNamespace(
            query_pointer=lambda: types.SimpleNamespace(mask=0, root_x=0, root_y=0))

    def get_input_focus(self):
        return types.SimpleNamespace(focus=41)

    def keysym_to_keycode(self, keysym):
        return {ord("W"): 38, ord("A"): 39}.get(keysym, 0)

    def screen(self):
        return types.SimpleNamespace(root=self.root)

    def query_keymap(self):
        self.trace.append(("query_keymap", tuple(sorted(self.down))))
        if self.fail_keymap_queries:
            self.fail_keymap_queries -= 1
            raise RuntimeError("synthetic keymap sample failure")
        bitmap = bytearray(32)
        for code in self.down:
            bitmap[code // 8] |= 1 << (code % 8)
        return bytes(bitmap)

    def sync(self):
        if self.fail_keyrelease_syncs:
            self.fail_keyrelease_syncs -= 1
            raise RuntimeError("synthetic key-release sync failure")
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
    def test_ordered_up_batch_has_no_keymap_query_between_original_ups(self):
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
            owner.call("down", lease, "A")
            display_instance.trace.clear()
            display_instance.drop_keyreleases = 1
            rows = owner.call("up_batch", lease, ["A", "W"])
            query_positions = [
                index for index, event in enumerate(display_instance.trace)
                if event[0] == "query_keymap"
            ]
            self.assertGreaterEqual(len(query_positions), 3)
            original_ups = [
                index for index, event in enumerate(display_instance.trace)
                if query_positions[0] < index < query_positions[1]
                and event[:2] == ("key_event", xlib.X.KeyRelease)
            ]
            self.assertEqual(len(original_ups), 2)
            self.assertEqual(
                [display_instance.trace[index][2] for index in original_ups], [39, 38])
            self.assertEqual(rows[0]["owner_thread_keyup_receipt"]["server_keyup_attempt_count"], 2)
            self.assertEqual(rows[1]["owner_thread_keyup_receipt"]["server_keyup_attempt_count"], 1)
            self.assertEqual(len(rows), 2)
            self.assertTrue(all(row["owner_thread_keyup_verified"] for row in rows))
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
            cleanup_after_success = owner.call("release", lease)
            self.assertTrue(cleanup_after_success["verified"])
            self.assertEqual(display_instance.keyrelease_attempts, 2)

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

            # Terminal cleanup must retain the earlier failed receipt while
            # independently retrying a key that remains observed down.
            display_instance.drop_keyreleases = 0
            cleanup_after_failure = owner.call("release", lease)
            self.assertTrue(cleanup_after_failure["verified"])
            self.assertEqual(cleanup_after_failure["keys_down"], [])
            self.assertEqual(display_instance.down, set())
            self.assertFalse(failed_receipt["server_keyup_verified"])
            self.assertEqual(len(cleanup_after_failure["key_release_attempts"]["38"]["attempts"]), 1)
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

    def test_single_keymap_sample_failure_is_captured_and_terminal_fails_closed(self):
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
            display_instance.fail_keymap_queries = 2  # pre-release and post-release sample
            transition = owner.call("up", lease, "W")
            receipt = next(row for row in owner.records
                           if row.get("event") == "owner_explicit_keyup")
            self.assertTrue(receipt["server_keyup_verified"])
            self.assertEqual(receipt["server_keyup_attempt_count"], 2)
            self.assertFalse(receipt["server_key_down_after_keyup"])
            self.assertIsNotNone(receipt["server_keyup_attempts"][0]["keymap_after_error"])
            self.assertEqual(display_instance.down, set())
            self.assertFalse(transition["owner_thread_keyup_verified"])
            self.assertEqual(transition["owner_thread_keyup_receipt"], receipt)
            self.assertFalse(transition["ordinary_release_candidate"])
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

    def test_terminal_release_sync_failure_still_attempts_other_keys_and_button(self):
        names = ("Xlib", "Xlib.X", "Xlib.XK", "Xlib.display", "Xlib.error", "Xlib.ext", "Xlib.ext.xtest")
        saved = {name: sys.modules.get(name) for name in names}
        display_instance = FakeDisplay()
        display_instance.intern_atom = lambda _name: 1
        class FakeWindow:
            id = 52
            def get_geometry(self): return types.SimpleNamespace(width=100, height=100)
            def get_attributes(self): return types.SimpleNamespace(map_state=2)
            def query_tree(self): return types.SimpleNamespace(parent=types.SimpleNamespace(id=1))
        root = types.SimpleNamespace(id=1, query_pointer=lambda: types.SimpleNamespace(mask=0, root_x=0, root_y=0),
            get_full_property=lambda *_args: types.SimpleNamespace(value=[52]),
            translate_coords=lambda *_args: types.SimpleNamespace(x=0, y=0, child=FakeWindow()))
        display_instance.screen = lambda: types.SimpleNamespace(root=root)
        display_instance.create_resource_object = lambda *_args: FakeWindow()
        xlib = types.ModuleType("Xlib")
        xlib.X = types.SimpleNamespace(KeyPress=2, KeyRelease=3, ButtonPress=4, ButtonRelease=5, Button1Mask=256, AnyPropertyType=0, IsViewable=2)
        xk = types.ModuleType("Xlib.XK"); xk.string_to_keysym = lambda key: ord(key)
        display = types.ModuleType("Xlib.display"); display.Display = lambda _name: display_instance
        error = types.ModuleType("Xlib.error"); error.BadWindow = type("BadWindow", (Exception,), {}); error.BadDrawable = type("BadDrawable", (Exception,), {})
        ext = types.ModuleType("Xlib.ext"); xtest = types.ModuleType("Xlib.ext.xtest")
        def fake_input(_display, event, code):
            if event == xlib.X.KeyPress: display_instance.down.add(code)
            elif event == xlib.X.KeyRelease: display_instance.keyrelease_attempts += 1; display_instance.down.discard(code)
            elif event == xlib.X.ButtonPress: root.query_pointer = lambda: types.SimpleNamespace(mask=256, root_x=0, root_y=0)
            elif event == xlib.X.ButtonRelease: root.query_pointer = lambda: types.SimpleNamespace(mask=0, root_x=0, root_y=0)
        xtest.fake_input = fake_input; ext.xtest = xtest
        xlib.XK, xlib.display, xlib.error, xlib.ext = xk, display, error, ext
        sys.modules.update({"Xlib": xlib, "Xlib.X": types.ModuleType("Xlib.X"), "Xlib.XK": xk, "Xlib.display": display, "Xlib.error": error, "Xlib.ext": ext, "Xlib.ext.xtest": xtest})
        owner = None
        try:
            sys.modules.pop("input_owner_v12", None)
            from input_owner_v12 import InputOwner
            owner = InputOwner(":fake"); lease = Lease(); lease.expected_surface = 52; lease.expected_geometry = [0,0,100,100]
            owner.call("down", lease, "W"); owner.call("down", lease, "A"); owner.call("button_down", lease, 1)
            display_instance.fail_keyrelease_syncs = 1
            with self.assertRaisesRegex(RuntimeError, "owner release not verified") as raised: owner.call("release", lease)
            record = raised.exception.owner_release_record
            self.assertFalse(record["verified"])
            self.assertTrue(any(row["source"] == "keyrelease_sync" for row in record["key_state_errors"]))
            self.assertEqual(display_instance.keyrelease_attempts, 2); self.assertEqual(display_instance.down, set())
            self.assertEqual(record["buttons_down"], [])
        finally:
            if owner is not None: owner.close()
            sys.modules.pop("input_owner_v12", None)
            for name, module in saved.items():
                if module is None: sys.modules.pop(name, None)
                else: sys.modules[name] = module

    def test_v15_successful_two_key_batch_retries_after_ordered_original_ups(self):
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

            class FakeBaseBackend:
                def execute(self, _step, _lease, _identifier, _index):
                    self.raw("W", True)
                    self.raw("A", True)
                    self.raw("A", False)
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
            display_instance.drop_keyreleases = 1
            backend = object.__new__(V15Backend)
            backend.owner = owner
            backend.held = set()
            backend.lease = lease
            events = []
            backend.emit = events.append
            backend._input_event_context = None
            backend._release_batch = threading.local()
            backend._last_release_batch_delivery = None
            executor = Executor(backend, events.append)
            executor.active = ("a04-compatible-success", lease, threading.current_thread())
            executor.release_watch_stops["a04-compatible-success"] = threading.Event()
            display_instance.trace.clear()
            executor._run_with_watcher_cleanup(
                "a04-compatible-success", [{"op": "fake-two-key-release"}], lease)

            terminal = next(row for row in events if row.get("event") == "terminal")
            batch_rows = [row for row in events
                          if row.get("release_batch_schema") == "input-release-batch-v3"]
            receipts = [row for row in owner.records
                        if row.get("event") == "owner_explicit_keyup"]
            query_positions = [
                index for index, event in enumerate(display_instance.trace)
                if event[0] == "query_keymap"
            ]
            initial_ups = [
                index for index, event in enumerate(display_instance.trace)
                if len(query_positions) >= 2 and query_positions[0] < index < query_positions[1]
                and event[:2] == ("key_event", xlib.X.KeyRelease)
            ]
            self.assertEqual(terminal["status"], "completed")
            self.assertTrue(terminal["release"]["verified"])
            self.assertEqual(terminal["release"]["keys_down"], [])
            self.assertEqual(len(batch_rows), 2)
            self.assertTrue(all(row["release_batch_complete"] for row in batch_rows))
            self.assertTrue(all(row["owner_transition_verified"] for row in batch_rows))
            self.assertTrue(all(row["owner_thread_keyup_verified"] for row in batch_rows))
            self.assertEqual([row["key"] for row in receipts], ["A", "W"])
            self.assertEqual([row["server_keyup_attempt_count"] for row in receipts], [2, 1])
            self.assertTrue(all(row["server_keyup_verified"] for row in receipts))
            self.assertEqual(len(initial_ups), 2)
            self.assertEqual(
                [display_instance.trace[index][2] for index in initial_ups], [39, 38])
            self.assertEqual(display_instance.keyrelease_attempts, 3)
            self.assertEqual(display_instance.down, set())
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
                    self.raw("A", True)
                    self.raw("A", False)
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
            display_instance.drop_keyreleases = 12
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
            display_instance.trace.clear()
            executor._run_with_watcher_cleanup(
                "persistent-loss", [{"op": "fake-key-up"}], lease)

            terminal = next(row for row in events if row.get("event") == "terminal")
            batch_rows = [row for row in events
                          if row.get("release_batch_schema") == "input-release-batch-v3"]
            explicit = [row for row in owner.records
                        if row.get("event") == "owner_explicit_keyup"]
            cleanup = next(row for row in owner.records
                           if row.get("event") == "owner_release")
            initial_ups = [
                index for index, event in enumerate(display_instance.trace)
                if event[:2] == ("key_event", xlib.X.KeyRelease)
            ][:2]
            self.assertEqual(terminal["status"], "failed")
            self.assertFalse(terminal["release"]["verified"])
            self.assertEqual(terminal["release"]["keys_down"], [38, 39])
            self.assertEqual(len(terminal["release"]["key_release_attempts"]["38"]["attempts"]), 3)
            self.assertEqual(len(terminal["release"]["key_release_attempts"]["39"]["attempts"]), 3)
            self.assertEqual(len(batch_rows), 2)
            self.assertTrue(all(row["release_batch_complete"] for row in batch_rows))
            self.assertTrue(all(row["owner_transition_verified"] is False for row in batch_rows))
            self.assertTrue(all(row["owner_thread_keyup_verified"] is False for row in batch_rows))
            self.assertEqual([row["key"] for row in explicit], ["A", "W"])
            self.assertTrue(all(row["server_keyup_attempt_count"] == 3 for row in explicit))
            self.assertTrue(all(row["server_keyup_verified"] is False for row in explicit))
            self.assertTrue(all(row["owner_thread_keyup_receipt"] in explicit for row in batch_rows))
            self.assertTrue(all(row["owned_keycodes_after_batch"] == [38, 39]
                                for row in batch_rows))
            self.assertEqual(len(initial_ups), 2)
            self.assertFalse(any(
                event[0] == "query_keymap"
                for event in display_instance.trace[initial_ups[0] + 1:initial_ups[1]]))
            self.assertEqual(cleanup["key_release_attempts"]["38"]["attempts"][0]["attempt"], 1)
            self.assertEqual(len(cleanup["key_release_attempts"]["38"]["attempts"]), 3)
            self.assertEqual(len(cleanup["key_release_attempts"]["39"]["attempts"]), 3)
            self.assertFalse(cleanup["verified"])
            self.assertEqual(cleanup["keys_down"], [38, 39])
            self.assertEqual(display_instance.keyrelease_attempts, 12)
            self.assertEqual(display_instance.down, {38, 39})
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

    def test_v15_batch_survives_pre_and_post_sample_failures_fail_closed(self):
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

            class FakeBaseBackend:
                def execute(self, _step, _lease, _identifier, _index):
                    self.raw("W", True)
                    self.raw("A", True)
                    self.raw("A", False)
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
            backend = object.__new__(V15Backend)
            backend.owner = owner
            backend.held = set()
            backend.lease = lease
            events = []
            backend.emit = events.append
            backend._input_event_context = None
            backend._release_batch = threading.local()
            backend._last_release_batch_delivery = None
            executor = Executor(backend, events.append)
            executor.active = ("sample-failures", lease, threading.current_thread())
            executor.release_watch_stops["sample-failures"] = threading.Event()

            # Query 1 is the batch pre-sample; query 2 is the post-batch
            # sample. Both fail, but the original ordered UPs must still run.
            display_instance.fail_keymap_queries = 100
            display_instance.trace.clear()
            executor._run_with_watcher_cleanup(
                "sample-failures", [{"op": "fake-two-key-release"}], lease)

            terminal = next(row for row in events if row.get("event") == "terminal")
            batch_rows = [row for row in events
                          if row.get("release_batch_schema") == "input-release-batch-v3"]
            receipts = [row for row in owner.records
                        if row.get("event") == "owner_explicit_keyup"]
            ups = [event[2] for event in display_instance.trace
                   if event[:2] == ("key_event", xlib.X.KeyRelease)]
            self.assertEqual(ups[:2], [39, 38])
            self.assertEqual([row["key"] for row in receipts], ["A", "W"])
            self.assertTrue(all(row["server_keyup_verified"] is False for row in receipts))
            self.assertTrue(all(row["server_key_down_after_keyup"] is None for row in receipts))
            self.assertTrue(all(row["server_keyup_attempts"][0]["keymap_before_error"]
                                for row in receipts))
            self.assertTrue(all(row["server_keyup_attempts"][0]["keymap_after_error"]
                                for row in receipts))
            self.assertEqual(len(batch_rows), 2)
            self.assertTrue(all(row["owner_thread_keyup_verified"] is False
                                for row in batch_rows))
            self.assertEqual(terminal["status"], "failed")
            self.assertFalse(terminal["release"]["verified"])
            self.assertEqual(terminal["release"]["keys_unknown"], [38, 39])
            self.assertTrue(terminal["release"]["key_state_errors"])
        finally:
            if owner is not None:
                display_instance.fail_keymap_queries = 0
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
