"""Deterministic X11-free interleaving test against the real v10 owner loop."""
import importlib.util
from pathlib import Path
import queue
import sys
import threading
import time
import types
import unittest

HERE = Path(__file__).resolve().parent


class FakeDisplay:
    def __init__(self, _name):
        self.down = set()
        self.events = []
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


class QueueCancel:
    """Cancellation becomes visible only after the up tuple is actually queued."""
    def __init__(self):
        self.event = threading.Event()

    def is_set(self):
        return self.event.is_set()


class OwnerGate:
    def __init__(self):
        self.up_enqueued = threading.Event()
        self.done_gates = queue.Queue()
        self.down_submitted = queue.Queue()


class GatedDone:
    def __init__(self, inner, release_event):
        self.inner = inner
        self.release_event = release_event

    def set(self):
        self.inner.set()
        if not self.release_event.wait(3):
            raise AssertionError("owner gate was not released")

    def wait(self, timeout=None):
        return self.inner.wait(timeout)


class GatedQueue(queue.Queue):
    def __init__(self, gate):
        super().__init__()
        self.gate = gate

    def get(self, *args, **kwargs):
        item = super().get(*args, **kwargs)
        if item[0] == "down":
            release_event = threading.Event()
            self.gate.done_gates.put(release_event)
            item = (*item[:3], GatedDone(item[3], release_event), item[4])
        return item

    def put(self, item, *args, **kwargs):
        if item[0] == "up":
            self.gate.up_enqueued.set()
            cancel = getattr(item[1], "cancel", None)
            if isinstance(cancel, QueueCancel):
                cancel.event.set()
        result = super().put(item, *args, **kwargs)
        if item[0] == "down":
            self.gate.down_submitted.put(True)
        return result


class RealOwnerQueueInterleavingTests(unittest.TestCase):
    def _run_cleanup_before_up(self, lease, cleanup_reason, next_lease=None,
                               cycles=64, verify_up=False,
                               expect_cleanup_intervened=False):
        names = (
            "Xlib", "Xlib.X", "Xlib.XK", "Xlib.display", "Xlib.error",
            "Xlib.ext", "Xlib.ext.xtest", "executor_v3", "input_owner_v10",
        )
        saved = {name: sys.modules.get(name) for name in names}
        gate = OwnerGate()
        try:
            xlib = types.ModuleType("Xlib")
            xconst = types.SimpleNamespace(KeyPress=2, KeyRelease=3,
                                           ButtonRelease=5, Button1Mask=256,
                                           AnyPropertyType=0)
            xlib.X = xconst
            xk = types.ModuleType("Xlib.XK")
            xk.string_to_keysym = lambda _key: 1
            display = types.ModuleType("Xlib.display")
            displays = []

            def create_display(name):
                instance = FakeDisplay(name)
                displays.append(instance)
                return instance

            display.Display = create_display
            error = types.ModuleType("Xlib.error")
            error.BadWindow = type("BadWindow", (Exception,), {})
            error.BadDrawable = type("BadDrawable", (Exception,), {})
            ext = types.ModuleType("Xlib.ext")
            xtest = types.ModuleType("Xlib.ext.xtest")

            def fake_input(connection, event, code):
                connection.events.append((event, code))
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

            real_queue = queue.Queue
            queue.Queue = lambda: GatedQueue(gate)
            try:
                wrapper = wrapper_module.InputOwner(":fake")
            finally:
                queue.Queue = real_queue
            try:
                admitted = wrapper.call("down", lease, "a")
                self.assertEqual(admitted["event"], "input_admission")
                down_gate = gate.done_gates.get(timeout=1)
                self.assertTrue(gate.down_submitted.get(timeout=1))
                if cleanup_reason == "cancelled":
                    if next_lease is None:
                        lease.cancel = QueueCancel()
                    else:
                        lease.cancel.set()

                if next_lease is not None:
                    previous = lease
                    previous_key = "a"
                    current = next_lease
                    max_markers = 0
                    for index in range(cycles):
                        previous.cancel.set()
                        key = f"b{index}"
                        result = {}
                        caller = threading.Thread(
                            target=lambda: result.setdefault(
                                "admission", wrapper.call("down", current, key)))
                        caller.start()
                        self.assertTrue(gate.down_submitted.get(timeout=1))
                        self.assertEqual(wrapper._inner.requests.qsize(), 1)
                        down_gate.set()
                        caller.join(2)
                        self.assertFalse(caller.is_alive())
                        if "error" in result:
                            raise result["error"]
                        next_admission = result.get("admission")
                        self.assertEqual(next_admission["event"], "input_admission")
                        down_gate = gate.done_gates.get(timeout=1)
                        self.assertTrue(any(
                            record.get("event") == "owner_release"
                            and record.get("reason") == cleanup_reason
                            for record in wrapper._inner.records
                        ))
                        self.assertEqual(set(wrapper._admission_records), {
                            (id(previous), previous_key), (id(current), key),
                        })
                        max_markers = max(max_markers,
                                          len(wrapper._admission_records))
                        previous_key = key
                        previous, current = current, Lease()
                    self.assertLessEqual(max_markers, 2)
                    if verify_up:
                        down_gate.set()
                        row = wrapper.call("up", previous, previous_key)
                        self.assertEqual(row["owner_cleanup_intervened"],
                                         expect_cleanup_intervened)
                        self.assertEqual(row["ordinary_release_candidate"],
                                         not expect_cleanup_intervened)
                    down_gate.set()
                    return

                result = {}

                def explicit_up():
                    try:
                        result["row"] = wrapper.call("up", lease, "a")
                    except BaseException as exc:
                        result["error"] = exc

                caller = threading.Thread(target=explicit_up)
                caller.start()
                self.assertTrue(gate.up_enqueued.wait(1), "up was not queued")
                if cleanup_reason == "expired":
                    remaining = max(0, (lease.deadline - time.perf_counter_ns()) / 1e9)
                    threading.Event().wait(remaining + 0.01)
                self.assertEqual(wrapper._inner.requests.qsize(), 1,
                                 "up must be pending before owner resumes")
                down_gate.set()
                caller.join(2)
                self.assertFalse(caller.is_alive(), "explicit up caller did not finish")
                if "error" in result:
                    raise result["error"]
                row = result["row"]
                self.assertTrue(row["owner_release_history_complete"])
                self.assertTrue(row["owner_cleanup_intervened"])
                self.assertFalse(row["ordinary_release_candidate"])
                self.assertFalse(row["owner_transition_verified"])
                self.assertTrue(any(
                    record.get("event") == "owner_release"
                    and record.get("reason") == cleanup_reason
                    for record in wrapper._inner.records
                ))
                self.assertEqual(displays[0].events,
                                 [(xconst.KeyPress, 38), (xconst.KeyRelease, 38)])
            finally:
                wrapper.close()
        finally:
            for name, module in saved.items():
                if module is None:
                    sys.modules.pop(name, None)
                else:
                    sys.modules[name] = module

    def test_cancel_cleanup_before_up_dequeue_is_not_verified_transition(self):
        self._run_cleanup_before_up(Lease(), "cancelled",
                                    expect_cleanup_intervened=True)

    def test_expiry_cleanup_before_up_dequeue_is_not_verified_transition(self):
        deadline = time.perf_counter_ns() + 1_000_000_000
        self._run_cleanup_before_up(Lease(deadline=deadline), "expired",
                                    expect_cleanup_intervened=True)

    def test_observed_async_cleanup_is_pruned_before_next_admission(self):
        self._run_cleanup_before_up(Lease(), "cancelled", next_lease=Lease())

    def test_same_deadline_prior_cleanup_does_not_misclassify_new_admission_up(self):
        deadline = time.perf_counter_ns() + 5_000_000_000
        self._run_cleanup_before_up(
            Lease(deadline=deadline), "cancelled",
            next_lease=Lease(deadline=deadline), cycles=1, verify_up=True)

    def test_different_deadline_prior_cleanup_preserves_new_admission_up(self):
        first_deadline = time.perf_counter_ns() + 5_000_000_000
        second_deadline = first_deadline + 1_000_000_000
        self._run_cleanup_before_up(
            Lease(deadline=first_deadline), "cancelled",
            next_lease=Lease(deadline=second_deadline), cycles=1, verify_up=True,
            expect_cleanup_intervened=False)


if __name__ == "__main__":
    unittest.main(verbosity=2)

