"""Exercise release-batch cancellation through the real V12/V4 owner."""
import importlib
import sys
import threading
import time
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
            queued_before_cancel = threading.Event()
            v12 = backend.owner._inner
            original_requests = v12.requests
            gate_owner_dequeue = threading.Event()
            owner_waiting_before_dequeue = threading.Event()
            cancel_after_enqueue = threading.Event()
            skip_one_dequeue = threading.Event()
            race_clock = {}

            class RequestGate:
                def put(self, request):
                    original_requests.put(request)
                    if request[0] == "up_batch":
                        raced.append(request[0])
                        race_clock["enqueued_ns"] = time.perf_counter_ns()
                        queued_before_cancel.set()
                        lease.cancel.set()
                        race_clock["cancel_requested_ns"] = time.perf_counter_ns()
                        cancel_after_enqueue.set()

                def get(self, timeout=None):
                    request = original_requests.get(timeout=timeout)
                    if (gate_owner_dequeue.is_set() and request[0] == "up_batch"
                            and not skip_one_dequeue.is_set()):
                        # The real RPC is already present in V12's queue. Put
                        # it back untouched and force one loop turn so the
                        # cancellation watcher performs cleanup before dequeue.
                        original_requests.put(request)
                        owner_waiting_before_dequeue.set()
                        if not cancel_after_enqueue.is_set():
                            raise AssertionError("owner dequeued before enqueue cancellation")
                        race_clock["owner_dequeue_deferred_ns"] = time.perf_counter_ns()
                        skip_one_dequeue.set()
                        raise queue.Empty
                    return request

            import queue
            v12.requests = RequestGate()
            gate_owner_dequeue.set()
            execution_error = []

            def run_execute():
                try:
                    backend.execute({}, lease.cancel, "program-race", 0)
                except BaseException as exc:
                    execution_error.append(exc)

            worker = threading.Thread(target=run_execute)
            worker.start()
            self.assertTrue(queued_before_cancel.wait(1), "up_batch was not enqueued")
            self.assertTrue(owner_waiting_before_dequeue.wait(1),
                            "owner did not reach the controlled dequeue boundary")
            self.assertTrue(lease.interrupted.wait(1), "cancellation cleanup did not finish")
            worker.join(2)
            self.assertFalse(worker.is_alive(), "backend execution did not finish")

            self.assertFalse(execution_error, execution_error)

            self.assertEqual(raced, ["up_batch"])
            self.assertTrue(queued_before_cancel.is_set())
            self.assertTrue(skip_one_dequeue.is_set())
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
            cleanup_verified_ns = row["owner_cleanup_record"]["verified_ns"]
            self.assertLess(race_clock["enqueued_ns"], race_clock["cancel_requested_ns"])
            self.assertLess(race_clock["cancel_requested_ns"],
                            race_clock["owner_dequeue_deferred_ns"])
            self.assertLess(race_clock["owner_dequeue_deferred_ns"], cleanup_verified_ns)
            self.assertLessEqual(cleanup_verified_ns, row["release_call_returned_ns"])
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
