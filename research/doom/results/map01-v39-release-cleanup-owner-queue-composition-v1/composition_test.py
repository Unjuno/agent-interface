"""Compose PR #7385 adapter with the real v10 owner loop under fake Xlib."""
import importlib.util
from pathlib import Path
import sys
import threading
import time
import types
import unittest
import json

ROOT = Path(__file__).resolve().parent
LIVE = ROOT / "research" / "live_control"
DOOM = ROOT / "research" / "doom"
OBSERVATIONS = []


class FakeDisplay:
    def __init__(self, _name):
        self.down = set()
        self.events = []
        self.closed = False
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
        return None

    def close(self):
        self.closed = True


class RaceCancel:
    """Let wrapper snapshot cancellation as false, then expose it to owner."""
    def __init__(self):
        self.event = threading.Event()
        self.caller = threading.get_ident()
        self.first = True

    def is_set(self):
        if threading.get_ident() == self.caller and self.first:
            self.first = False
            self.event.set()
            return False
        return self.event.is_set()


class Lease:
    def __init__(self, deadline_ns=None):
        self.intent_token = "integration-intent"
        self.deadline = deadline_ns or time.perf_counter_ns() + 5_000_000_000
        self.cancel = threading.Event()
        self.expected_focus = 41
        self.focus_invalid = False

    def check(self):
        if time.perf_counter_ns() >= self.deadline:
            raise RuntimeError("expired")


def install_mock_xlib(backend_path):
    names = ("Xlib", "Xlib.X", "Xlib.XK", "Xlib.display", "Xlib.error",
             "Xlib.ext", "Xlib.ext.xtest", "executor_v3", "input_owner_v10",
             "input_transition_owner_v3", "doom_typed_release_backend_v1",
             "doom_typed_release_backend_v3_under_test")
    saved = {name: sys.modules.get(name) for name in names}
    xlib = types.ModuleType("Xlib")
    xconst = types.SimpleNamespace(KeyPress=2, KeyRelease=3, ButtonRelease=5,
                                   Button1Mask=256, AnyPropertyType=0)
    xlib.X = xconst
    xk = types.ModuleType("Xlib.XK")
    xk.string_to_keysym = lambda _key: 1
    display = types.ModuleType("Xlib.display")
    displays = []

    def create_display(name):
        item = FakeDisplay(name)
        displays.append(item)
        return item

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
    base = types.ModuleType("doom_typed_release_backend_v1")

    class Previous:
        pass

    base.Backend = Previous
    base.suite = object()
    sys.modules.update({
        "Xlib": xlib, "Xlib.X": types.ModuleType("Xlib.X"), "Xlib.XK": xk,
        "Xlib.display": display, "Xlib.error": error, "Xlib.ext": ext,
        "Xlib.ext.xtest": xtest, "executor_v3": executor,
        "doom_typed_release_backend_v1": base,
    })
    owner_spec = importlib.util.spec_from_file_location(
        "input_owner_v10", LIVE / "input_owner_v10.py")
    owner_module = importlib.util.module_from_spec(owner_spec)
    sys.modules["input_owner_v10"] = owner_module
    owner_spec.loader.exec_module(owner_module)
    wrapper_spec = importlib.util.spec_from_file_location(
        "input_transition_owner_v3", LIVE / "input_transition_owner_v3.py")
    wrapper_module = importlib.util.module_from_spec(wrapper_spec)
    sys.modules["input_transition_owner_v3"] = wrapper_module
    wrapper_spec.loader.exec_module(wrapper_module)
    backend_spec = importlib.util.spec_from_file_location(
        "doom_typed_release_backend_v3_under_test", backend_path)
    backend_module = importlib.util.module_from_spec(backend_spec)
    sys.modules[backend_spec.name] = backend_module
    backend_spec.loader.exec_module(backend_module)
    return saved, wrapper_module, backend_module, displays, xconst


def restore_modules(saved):
    for name, module in saved.items():
        if module is None:
            sys.modules.pop(name, None)
        else:
            sys.modules[name] = module


class BackendHarness:
    def __init__(self, owner, lease):
        self.owner = owner
        self.lease = lease
        self.held = {"a"}
        self._release_batch = threading.local()
        self._release_batch.context = {"rows": [], "identifier": "queue-race",
                                       "step": 0}
        self.emitted = []
        self.emit = self.emitted.append


class RealOwnerCompositionTests(unittest.TestCase):
    def _run_race(self, cause, *, candidate=True):
        backend_path = DOOM / ("doom_typed_release_backend_v3.py" if candidate else
                               "doom_typed_release_backend_v3_parent.py")
        saved, wrapper_module, backend_module, displays, xconst = install_mock_xlib(
            backend_path)
        wrapper = None
        try:
            if cause == "expired":
                lease = Lease(time.perf_counter_ns() + 100_000_000)
            else:
                lease = Lease()
            wrapper = wrapper_module.InputOwner(":fake")
            admission = wrapper.call("down", lease, "a")
            self.assertEqual(admission["event"], "input_admission")
            if cause == "cancelled":
                lease.cancel = RaceCancel()
            inner = wrapper._inner
            original_call = inner.call

            def queue_up_after_cleanup(operation, call_lease=None, key=None):
                if operation == "up":
                    end = time.monotonic() + 2
                    while not any(
                        isinstance(record, dict)
                        and record.get("event") == "owner_release"
                        and record.get("reason") == cause
                        for record in inner.records
                    ):
                        if time.monotonic() >= end:
                            raise AssertionError(f"{cause} cleanup did not precede up")
                        threading.Event().wait(0.001)
                return original_call(operation, call_lease, key)

            inner.call = queue_up_after_cleanup
            harness = BackendHarness(wrapper, lease)
            adapter_obj = backend_module.Backend.__new__(backend_module.Backend)
            adapter_obj.owner = harness.owner
            adapter_obj.lease = harness.lease
            adapter_obj.held = harness.held
            adapter_obj._release_batch = harness._release_batch
            adapter_obj.emit = harness.emit

            adapter_obj.raw("a", False)

            self.assertEqual(len(harness.emitted), 1)
            receipt = harness.emitted[0]
            if candidate:
                self.assertTrue(receipt["lease_time_valid_at_request"])
                if cause == "cancelled":
                    self.assertFalse(receipt["cancel_requested_at_request"])
                self.assertTrue(receipt["owner_cleanup_records_available"])
                self.assertTrue(receipt["owner_cleanup_overlapped_release_call"])
                self.assertFalse(receipt["ordinary_release_candidate"])
                self.assertFalse(receipt["owner_transition_verified"])
            else:
                # Red-first control: the exact #7378 parent misses the queue
                # cleanup and falsely verifies the later explicit-up call.
                cleanup_ns = next(r["verified_ns"] for r in wrapper.records
                                  if r.get("event") == "owner_release")
                self.assertLessEqual(receipt["release_call_started_ns"], cleanup_ns)
                self.assertLessEqual(cleanup_ns, receipt["release_call_returned_ns"])
                self.assertTrue(receipt["ordinary_release_candidate"])
                self.assertTrue(receipt["owner_transition_verified"])
            self.assertEqual(displays[0].events,
                             [(xconst.KeyPress, 38), (xconst.KeyRelease, 38)])
            self.assertEqual(harness.held, set())
            owner_release = next(r for r in wrapper.records
                                 if r.get("event") == "owner_release")
            OBSERVATIONS.append({
                "candidate": candidate,
                "cause": cause,
                "owner_release_reason": owner_release.get("reason"),
                "owner_release_verified": owner_release.get("verified"),
                "owner_release_verified_ns": owner_release.get("verified_ns"),
                "release_call_started_ns": receipt.get("release_call_started_ns"),
                "release_call_returned_ns": receipt.get("release_call_returned_ns"),
                "owner_cleanup_overlapped_release_call": receipt.get(
                    "owner_cleanup_overlapped_release_call"),
                "ordinary_release_candidate": receipt.get("ordinary_release_candidate"),
                "owner_transition_verified": receipt.get("owner_transition_verified"),
                "xlib_event_count": len(displays[0].events),
                "xlib_event_kinds": [event for event, _ in displays[0].events],
            })
            return {
                "cause": cause,
                "receipt": receipt,
                "owner_records": wrapper.records,
                "xlib_events": displays[0].events,
            }
        finally:
            if wrapper is not None:
                wrapper.close()
            restore_modules(saved)

    def test_cancel_cleanup_before_queued_up_is_detected_by_candidate(self):
        result = self._run_race("cancelled")
        self.assertTrue(any(r.get("reason") == "cancelled"
                            for r in result["owner_records"]))

    def test_expiry_cleanup_before_queued_up_is_detected_by_candidate(self):
        result = self._run_race("expired")
        self.assertTrue(any(r.get("reason") == "expired"
                            for r in result["owner_records"]))

    def test_exact_parent_false_positive_for_cancel_queue_interleaving(self):
        result = self._run_race("cancelled", candidate=False)
        self.assertTrue(any(r.get("reason") == "cancelled"
                            for r in result["owner_records"]))

    def test_exact_parent_false_positive_for_expiry_queue_interleaving(self):
        result = self._run_race("expired", candidate=False)
        self.assertTrue(any(r.get("reason") == "expired"
                            for r in result["owner_records"]))

    def test_candidate_preserves_ordinary_release_without_cleanup(self):
        saved, wrapper_module, backend_module, displays, xconst = install_mock_xlib(
            DOOM / "doom_typed_release_backend_v3.py")
        wrapper = None
        try:
            lease = Lease()
            wrapper = wrapper_module.InputOwner(":fake")
            wrapper.call("down", lease, "a")
            harness = BackendHarness(wrapper, lease)
            adapter_obj = backend_module.Backend.__new__(backend_module.Backend)
            adapter_obj.owner = harness.owner
            adapter_obj.lease = harness.lease
            adapter_obj.held = harness.held
            adapter_obj._release_batch = harness._release_batch
            adapter_obj.emit = harness.emit
            adapter_obj.raw("a", False)
            receipt = harness.emitted[0]
            self.assertTrue(receipt["owner_cleanup_records_available"])
            self.assertFalse(receipt["owner_cleanup_overlapped_release_call"])
            self.assertTrue(receipt["ordinary_release_candidate"])
            self.assertTrue(receipt["owner_transition_verified"])
            self.assertEqual(displays[0].events,
                             [(xconst.KeyPress, 38), (xconst.KeyRelease, 38)])
            OBSERVATIONS.append({
                "candidate": True,
                "cause": "none",
                "owner_cleanup_records_available": receipt.get(
                    "owner_cleanup_records_available"),
                "owner_cleanup_overlapped_release_call": receipt.get(
                    "owner_cleanup_overlapped_release_call"),
                "ordinary_release_candidate": receipt.get("ordinary_release_candidate"),
                "owner_transition_verified": receipt.get("owner_transition_verified"),
                "xlib_event_count": len(displays[0].events),
                "xlib_event_kinds": [event for event, _ in displays[0].events],
            })
        finally:
            if wrapper is not None:
                wrapper.close()
            restore_modules(saved)


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(RealOwnerCompositionTests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    (ROOT / "results" / "composition.json").write_text(
        json.dumps({"tests_run": result.testsRun,
                    "failures": len(result.failures),
                    "errors": len(result.errors),
                    "observations": OBSERVATIONS}, indent=2, sort_keys=True) + "\n",
        encoding="utf-8")
    if not result.wasSuccessful():
        raise SystemExit(1)
