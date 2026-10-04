"""Deterministic X11-free interleaving test against the real v10 owner loop."""
import importlib.util
from pathlib import Path
import sys
import threading
import time
import types
import unittest

HERE = Path(__file__).resolve().parent


class FakeDisplay:
    def __init__(self, _name):
        self.down = set()
        self.closed = False
        self._root = types.SimpleNamespace(query_pointer=lambda: types.SimpleNamespace(mask=0))

    def get_input_focus(self):
        return types.SimpleNamespace(focus=41)

    def keysym_to_keycode(self, _keysym):
        return 38

    def screen(self):
        return types.SimpleNamespace(root=self._root)

    def query_keymap(self):
        bitmap = bytearray(32)
        for code in self.down:
            bitmap[code // 8] |= 1 << (code % 8)
        return bytes(bitmap)

    def sync(self):
        return None

    def close(self):
        self.closed = True


class RaceCancel:
    """Expose false to the wrapper snapshot, then make cancellation visible."""
    def __init__(self):
        self.event = threading.Event()
        self.caller_thread = threading.get_ident()
        self.first_caller_read = True

    def is_set(self):
        if threading.get_ident() == self.caller_thread and self.first_caller_read:
            self.first_caller_read = False
            self.event.set()
            return False
        return self.event.is_set()


class Lease:
    def __init__(self, deadline=None):
        self.intent_token = "race-intent"
        self.deadline = deadline or time.perf_counter_ns() + 5_000_000_000
        self.cancel = threading.Event()
        self.expected_focus = 41
        self.focus_invalid = False

    def check(self):
        if time.perf_counter_ns() >= self.deadline:
            raise RuntimeError("expired")


class RealOwnerQueueInterleavingTests(unittest.TestCase):
    def _run_cleanup_before_up(self, lease, cleanup_reason):
        names = (
            "Xlib", "Xlib.X", "Xlib.XK", "Xlib.display", "Xlib.error",
            "Xlib.ext", "Xlib.ext.xtest", "executor_v3", "input_owner_v10",
        )
        saved = {name: sys.modules.get(name) for name in names}
        try:
            xlib = types.ModuleType("Xlib")
            xconst = types.SimpleNamespace(KeyPress=2, KeyRelease=3,
                                           ButtonRelease=5, Button1Mask=256,
                                           AnyPropertyType=0)
            xlib.X = xconst
            xk = types.ModuleType("Xlib.XK")
            xk.string_to_keysym = lambda _key: 1
            display = types.ModuleType("Xlib.display")
            display.Display = FakeDisplay
            error = types.ModuleType("Xlib.error")
            error.BadWindow = type("BadWindow", (Exception,), {})
            error.BadDrawable = type("BadDrawable", (Exception,), {})
            ext = types.ModuleType("Xlib.ext")
            xtest = types.ModuleType("Xlib.ext.xtest")

            def fake_input(connection, event, code):
                if event == xconst.KeyPress:
                    connection.down.add(code)
                elif event == xconst.KeyRelease:
                    connection.down.discard(code)

            xtest.fake_input = fake_input
            ext.xtest = xtest
            xlib.XK, xlib.display, xlib.error, xlib.ext = xk, display, error, ext
            executor = types.ModuleType("executor_v3")
            executor.Cancelled = type("Cancelled", (Exception,), {})
            executor.DecisionRequired = type("DecisionRequired", (Exception,), {})
            sys.modules.update({
                "Xlib": xlib, "Xlib.X": types.ModuleType("Xlib.X"),
                "Xlib.XK": xk, "Xlib.display": display, "Xlib.error": error,
                "Xlib.ext": ext, "Xlib.ext.xtest": xtest, "executor_v3": executor,
            })

            owner_spec = importlib.util.spec_from_file_location(
                "input_owner_v10", HERE / "input_owner_v10.py")
            owner_module = importlib.util.module_from_spec(owner_spec)
            sys.modules["input_owner_v10"] = owner_module
            owner_spec.loader.exec_module(owner_module)

            wrapper_spec = importlib.util.spec_from_file_location(
                "input_transition_owner_v3_queue_test", HERE / "input_transition_owner_v3.py")
            wrapper_module = importlib.util.module_from_spec(wrapper_spec)
            wrapper_spec.loader.exec_module(wrapper_module)

            wrapper = wrapper_module.InputOwner(":fake")
            try:
                admitted = wrapper.call("down", lease, "a")
                self.assertEqual(admitted["event"], "input_admission")
                if cleanup_reason == "cancelled":
                    lease.cancel = RaceCancel()

                inner = wrapper._inner
                original_call = inner.call

                def delay_up_until_owner_cleanup(operation, call_lease=None, key=None):
                    if operation == "up":
                        limit = time.monotonic() + 1
                        while not any(
                            record.get("event") == "owner_release"
                            and record.get("reason") == cleanup_reason
                            for record in inner.records
                        ):
                            if time.monotonic() >= limit:
                                raise AssertionError(
                                    f"{cleanup_reason} cleanup did not precede queued up")
                            threading.Event().wait(0.001)
                    return original_call(operation, call_lease, key)

                inner.call = delay_up_until_owner_cleanup
                row = wrapper.call("up", lease, "a")
                self.assertTrue(row["owner_release_history_complete"])
                self.assertTrue(row["owner_cleanup_intervened"])
                self.assertFalse(row["ordinary_release_candidate"])
                self.assertFalse(row["owner_transition_verified"])
            finally:
                wrapper.close()
        finally:
            for name, module in saved.items():
                if module is None:
                    sys.modules.pop(name, None)
                else:
                    sys.modules[name] = module

    def test_cancel_cleanup_before_up_dequeue_is_not_verified_transition(self):
        self._run_cleanup_before_up(Lease(), "cancelled")

    def test_expiry_cleanup_before_up_dequeue_is_not_verified_transition(self):
        deadline = time.perf_counter_ns() + 100_000_000
        self._run_cleanup_before_up(Lease(deadline=deadline), "expired")


if __name__ == "__main__":
    unittest.main(verbosity=2)
