"""Exercise release-batch cancellation through the real V12/V4 owner."""
import importlib
import sys
import threading
import types
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DOOM = ROOT / "research" / "doom"
LIVE = ROOT / "research" / "live_control"
sys.path[:0] = [str(DOOM), str(LIVE)]


class Lease:
    def __init__(self):
        self.intent_token = "composition-test"
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


class Display:
    def __init__(self):
        self.down = set()
        self.keyrelease_attempts = 0
        self.trace = []
        self.keypress_delivered = threading.Event()
        self.release_cleanup_finished = threading.Event()
        self.root = types.SimpleNamespace(
            query_pointer=lambda: types.SimpleNamespace(mask=0, root_x=0, root_y=0)
        )

    def get_input_focus(self):
        return types.SimpleNamespace(focus=41)

    def keysym_to_keycode(self, keysym):
        return {ord("W"): 38}.get(keysym, 0)

    def screen(self):
        return types.SimpleNamespace(root=self.root)

    def query_keymap(self):
        bitmap = bytearray(32)
        for code in self.down:
            bitmap[code // 8] |= 1 << (code % 8)
        return bytes(bitmap)

    def sync(self):
        self.trace.append(("sync", tuple(sorted(self.down))))
        if not self.down and self.keypress_delivered.is_set():
            self.release_cleanup_finished.set()

    def close(self):
        pass


class BaseBackend:
    def __init__(self, session, _out, emit, _signal_readers):
        self.owner = types.SimpleNamespace(close=lambda: None)
        self.held = set()
        self.lease = None
        self._input_event_context = None
        self.emit = emit

    def execute(self, _step, _cancel, identifier, index):
        self._input_event_context = (identifier, index)
        self.raw("W", True)
        self.raw("W", False)

    def release_all(self):
        return self.owner.call("release", self.lease)


class ReleaseBatchOwnerRaceTests(unittest.TestCase):
    def test_cleanup_winning_inside_up_batch_is_joined_through_backend(self):
        xlib_names = (
            "Xlib", "Xlib.X", "Xlib.XK", "Xlib.display", "Xlib.error",
            "Xlib.ext", "Xlib.ext.xtest",
        )
        module_names = (
            *xlib_names, "input_owner_v12", "input_transition_owner_v3",
            "input_transition_owner_v4", "doom_typed_release_backend_v2",
            "doom_owner_thread_release_batch_backend_v1",
        )
        saved = {name: sys.modules.get(name) for name in module_names}
        display = Display()

        xlib = types.ModuleType("Xlib")
        xlib.X = types.SimpleNamespace(
            KeyPress=2, KeyRelease=3, ButtonRelease=5,
            Button1Mask=256, AnyPropertyType=0,
        )
        xk = types.ModuleType("Xlib.XK")
        xk.string_to_keysym = lambda key: ord(key)
        xdisplay = types.ModuleType("Xlib.display")
        xdisplay.Display = lambda _name: display
        xerror = types.ModuleType("Xlib.error")
        xerror.BadWindow = type("BadWindow", (Exception,), {})
        xerror.BadDrawable = type("BadDrawable", (Exception,), {})
        xext = types.ModuleType("Xlib.ext")
        xtest = types.ModuleType("Xlib.ext.xtest")

        def fake_input(_display, event, keycode):
            if event == xlib.X.KeyPress:
                display.down.add(keycode)
                display.keypress_delivered.set()
            elif event == xlib.X.KeyRelease:
                display.keyrelease_attempts += 1
                display.down.discard(keycode)

        xtest.fake_input = fake_input
        xext.xtest = xtest
        xlib.XK, xlib.display, xlib.error, xlib.ext = xk, xdisplay, xerror, xext
        sys.modules.update({
            "Xlib": xlib, "Xlib.X": types.ModuleType("Xlib.X"),
            "Xlib.XK": xk, "Xlib.display": xdisplay,
            "Xlib.error": xerror, "Xlib.ext": xext,
            "Xlib.ext.xtest": xtest,
        })

        base_module = types.ModuleType("doom_typed_release_backend_v2")
        base_module.Backend = BaseBackend
        base_module.suite = object()
        sys.modules["doom_typed_release_backend_v2"] = base_module

        backend = None
        try:
            for name in module_names:
                if name not in xlib_names and name != "doom_typed_release_backend_v2":
                    sys.modules.pop(name, None)
            backend_module = importlib.import_module(
                "doom_owner_thread_release_batch_backend_v1"
            )
            emitted = []
            backend = backend_module.Backend(
                types.SimpleNamespace(name=":fake"), None, emitted.append, {}
            )
            lease = Lease()
            backend.lease = lease
            raced = []
            # Block only the owner's response to the admitted key-down. This
            # lets the real backend append its UP and enqueue up_batch before
            # cancellation cleanup is allowed to win V12's request loop.
            entered_admission = threading.Event()
            permit_admission_return = threading.Event()
            real_call = backend.owner.call
            original_inner_call = backend.owner._inner.call

            queued_before_cancel = threading.Event()

            def cancel_after_backend_precheck(operation, call_lease=None, key=None):
                if operation == "up_batch" and not raced:
                    raced.append(operation)
                    call_lease.cancel.set()
                    if not call_lease.interrupted.wait(1):
                        raise AssertionError("owner cleanup did not complete")
                return real_call(operation, call_lease, key)

            # Hold the actual V12 batch RPC after V3 has admitted it. The
            # cancellation watcher can then release the key before V12
            # dequeues the already-enqueued up_batch request.
            def hold_queued_batch(operation, call_lease=None, key=None):
                if operation == "up_batch":
                    queued_before_cancel.set()
                    if not permit_queued_batch.wait(1):
                        raise AssertionError("test did not release queued up_batch")
                return original_inner_call(operation, call_lease, key)

            permit_queued_batch = threading.Event()
            backend.owner._inner.call = hold_queued_batch

            def hold_admission_reply(operation, call_lease=None, key=None):
                result = real_call(operation, call_lease, key)
                if operation == "down":
                    entered_admission.set()
                    if not permit_admission_return.wait(1):
                        raise AssertionError("test did not release admitted key-down")
                return result

            backend.owner.call = hold_admission_reply
            execution_error = []

            def run_execute():
                try:
                    backend.execute({}, lease.cancel, "program-race", 0)
                except BaseException as exc:
                    execution_error.append(exc)

            worker = threading.Thread(target=run_execute)
            worker.start()
            self.assertTrue(entered_admission.wait(1), "key-down did not reach owner")
            backend.owner.call = cancel_after_backend_precheck
            permit_admission_return.set()
            self.assertTrue(queued_before_cancel.wait(1), "up_batch was not enqueued")
            self.assertTrue(lease.interrupted.wait(1), "cancellation cleanup did not finish")
            permit_queued_batch.set()
            worker.join(2)
            self.assertFalse(worker.is_alive(), "backend execution did not finish")

            self.assertFalse(execution_error, execution_error)

            self.assertEqual(raced, ["up_batch"])
            self.assertTrue(queued_before_cancel.is_set())
            self.assertTrue(display.keypress_delivered.is_set())
            self.assertTrue(display.release_cleanup_finished.is_set())
            self.assertTrue(lease.interruptions[-1]["verified"])
            self.assertEqual(lease.interruptions[-1]["keys_down"], [])
            self.assertEqual(display.down, set())
            rows = [row for row in emitted if row.get("event") == "input_release_transition"]
            self.assertEqual(len(rows), 1)
            row = rows[0]
            self.assertTrue(row["owner_cleanup_release_verified"])
            self.assertTrue(row["owner_cleanup_intervened"])
            self.assertFalse(row["owner_thread_keyup_verified"])
            self.assertFalse(row["ordinary_release_candidate"])
            self.assertFalse(row["grants_input_authority"])
        finally:
            if backend is not None:
                backend.owner.close()
            for name, module in saved.items():
                if module is None:
                    sys.modules.pop(name, None)
                else:
                    sys.modules[name] = module


if __name__ == "__main__":
    unittest.main(verbosity=2)
