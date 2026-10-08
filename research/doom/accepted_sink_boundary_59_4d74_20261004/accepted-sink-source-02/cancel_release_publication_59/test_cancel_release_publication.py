"""Deterministic regression for cancellation release publication; no X server needed."""
import sys
import threading
import time
import types
import unittest
from pathlib import Path

SERVER = {"down": set(), "lock": threading.Lock()}
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


class FakeRoot:
    def query_pointer(self):
        return types.SimpleNamespace(mask=0, root_x=0, root_y=0)


class FakeDisplay:
    def __init__(self, _name=None):
        self.root = FakeRoot()

    def get_input_focus(self):
        return types.SimpleNamespace(focus=42)

    def keysym_to_keycode(self, _keysym):
        return 25

    def sync(self):
        return None

    def query_keymap(self):
        bitmap = bytearray(32)
        with SERVER["lock"]:
            for code in SERVER["down"]:
                bitmap[code // 8] |= 1 << (code % 8)
        return bytes(bitmap)

    def screen(self):
        return types.SimpleNamespace(root=self.root)

    def close(self):
        return None


def fake_input(_display, event_type, code, **_kwargs):
    with SERVER["lock"]:
        if event_type == 2:
            SERVER["down"].add(code)
        elif event_type == 3:
            SERVER["down"].discard(code)
        else:
            raise AssertionError(f"unexpected XTest event: {event_type}")


def install_fake_xlib():
    x = types.SimpleNamespace(KeyPress=2, KeyRelease=3, ButtonRelease=5,
                              ButtonPress=4, Button1Mask=1, AnyPropertyType=0,
                              IsViewable=2, MotionNotify=6)
    xk = types.SimpleNamespace(string_to_keysym=lambda value: ord(value[0]))
    display = types.SimpleNamespace(Display=FakeDisplay)
    error = types.SimpleNamespace(BadWindow=type("BadWindow", (Exception,), {}),
                                  BadDrawable=type("BadDrawable", (Exception,), {}))
    xlib = types.ModuleType("Xlib")
    xlib.__path__ = []
    xlib.X, xlib.XK, xlib.display, xlib.error = x, xk, display, error
    ext = types.ModuleType("Xlib.ext")
    ext.__path__ = []
    xtest = types.ModuleType("Xlib.ext.xtest")
    xtest.fake_input = fake_input
    sys.modules.update({"Xlib": xlib, "Xlib.ext": ext, "Xlib.ext.xtest": xtest})


class Backend:
    def __init__(self, owner):
        self.owner, self.sequence, self.lease = owner, 1, None
        self.admission, self.held = None, set()

    def validate(self, steps):
        if steps != [{"op": "hold_w_until_cancel"}]:
            raise AssertionError(steps)

    def execute(self, step, lease, identifier, index):
        lease.expected_focus = 42
        self.admission = self.owner.call("down", lease, "w")
        self.held.add("w")
        lease.wait(10)

    def release_all(self):
        # Exact body in research/live_control/session_v5.py.
        result = self.owner.call("release", getattr(self, "lease", None))
        self.held.clear()
        gate = getattr(self, "release_gate", None)
        if gate is not None:
            gate.wait(2)
        return result


class CancelReleasePublicationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        install_fake_xlib()
        from executor_v12 import Executor
        from input_owner_v10 import InputOwner
        cls.Executor, cls.InputOwner = Executor, InputOwner

    def test_cancel_while_key_held_publishes_receipt_before_terminal(self):
        SERVER["down"].clear()
        owner = self.InputOwner(None)
        backend = Backend(owner)
        events = []
        executor = self.Executor(backend, events.append)
        watcher_started = threading.Event()
        watcher_gate = threading.Event()
        publish = executor._publish_release
        def gated_publish(identifier, lease):
            watcher_started.set()
            watcher_gate.wait(2)
            return publish(identifier, lease)
        executor._publish_release = gated_publish
        try:
            executor.submit("cancel-release-test", [{"op": "hold_w_until_cancel"}], 1,
                            time.perf_counter_ns() + 10_000_000_000)
            deadline = time.monotonic() + 2
            while backend.admission is None and time.monotonic() < deadline:
                time.sleep(.001)
            self.assertIsNotNone(backend.admission)
            self.assertEqual(backend.admission["event"], "input_admission")
            self.assertTrue(executor.cancel("cancel-release-test"))
            self.assertTrue(watcher_started.wait(2))
            worker = executor.active[2]
            worker.join(3)
            self.assertFalse(worker.is_alive())
            watcher_gate.set()
            for watcher in executor.release_watchers:
                watcher.join(3)
            self.assertFalse(worker.is_alive())
            self.assertTrue(all(not watcher.is_alive() for watcher in executor.release_watchers))
            release_events = [e for e in events if e["event"] == "input_released"]
            release = release_events[0] if len(release_events) == 1 else None
            terminal = next((e for e in events if e["event"] == "terminal"), None)
            self.last_event_order = [e["event"] for e in events]
            self.last_terminal_interruption = terminal.get("interruption") if terminal else None
            self.last_events = events
            self.assertEqual(len(release_events), 1, events)
            self.assertIsNotNone(terminal, events)
            self.assertLess(events.index(release), events.index(terminal))
            self.assertEqual(terminal["status"], "cancelled")
            self.assertEqual(release["owner_release"]["reason"], "cancelled")
            self.assertEqual(release["intent_token"], terminal["interruption"]["intent_token"])
            self.assertEqual(release["owner_release"], terminal["interruption"]["record"])
            self.assertIs(release["owner_release"]["verified"], True)
            self.assertEqual(release["owner_release"]["keys_down"], [])
            self.assertFalse(SERVER["down"])
        finally:
            watcher_gate.set()
            executor.close()
            owner.close()

    def test_release_emitter_failure_is_not_retried_before_terminal(self):
        SERVER["down"].clear()
        owner = self.InputOwner(None)
        backend = Backend(owner)
        backend.release_gate = threading.Event()
        events, attempts = [], []
        def emit(event):
            if event.get("event") in ("input_released", "input_release_unverified"):
                attempts.append(event)
                if len(attempts) == 1:
                    try:
                        raise OSError("sink rejected release event")
                    finally:
                        backend.release_gate.set()
            events.append(event)
        executor = self.Executor(backend, emit)
        try:
            executor.submit("release-emitter-retry", [{"op": "hold_w_until_cancel"}], 1,
                            time.perf_counter_ns() + 10_000_000_000)
            deadline = time.monotonic() + 2
            while backend.admission is None and time.monotonic() < deadline:
                time.sleep(.001)
            self.assertIsNotNone(backend.admission)
            self.assertTrue(executor.cancel("release-emitter-retry"))
            worker = executor.active[2]
            worker.join(3)
            for watcher in executor.release_watchers:
                watcher.join(3)
            terminal = next((e for e in events if e.get("event") == "terminal"), None)
            release_events = [e for e in events if e.get("event") == "input_released"]
            self.assertEqual(len(attempts), 1)
            self.assertEqual(len(release_events), 0)
            self.assertIsNotNone(terminal, events)
            self.assertEqual(terminal["input_release_publication"]["status"],
                             "delivery_unknown")
            self.assertFalse(worker.is_alive())
            self.assertTrue(all(not watcher.is_alive() for watcher in executor.release_watchers))
            self.assertIsNone(executor.active)
            self.assertIn("release-emitter-retry", executor.release_publication_attempted_ids)
            self.assertNotIn("release-emitter-retry", executor.published_release_ids)
        finally:
            executor.close()
            owner.close()

    def test_persistent_release_emitter_failure_is_reported_on_terminal(self):
        SERVER["down"].clear()
        owner = self.InputOwner(None)
        backend = Backend(owner)
        events = []
        def emit(event):
            if event.get("event") in ("input_released", "input_release_unverified"):
                raise OSError("sink unavailable")
            events.append(event)
        executor = self.Executor(backend, emit)
        try:
            executor.submit("release-emitter-unavailable", [{"op": "hold_w_until_cancel"}], 1,
                            time.perf_counter_ns() + 10_000_000_000)
            deadline = time.monotonic() + 2
            while backend.admission is None and time.monotonic() < deadline:
                time.sleep(.001)
            self.assertIsNotNone(backend.admission)
            self.assertTrue(executor.cancel("release-emitter-unavailable"))
            worker = executor.active[2]
            worker.join(3)
            terminal = next((e for e in events if e.get("event") == "terminal"), None)
            self.assertIsNotNone(terminal, events)
            self.assertEqual(terminal["input_release_publication"]["status"], "delivery_unknown")
            self.assertEqual(terminal["input_release_publication"]["error"]["type"], "OSError")
            self.assertFalse(worker.is_alive())
            self.assertIsNone(executor.active)
            self.assertNotIn("release-emitter-unavailable", executor.published_release_ids)
            self.assertNotIn("release-emitter-unavailable", executor.release_publication_errors)
        finally:
            executor.close()
            owner.close()

    def test_terminal_emitter_failure_is_locally_reported_and_fails_closed(self):
        SERVER["down"].clear()
        owner = self.InputOwner(None)
        backend = Backend(owner)
        events, thread_errors = [], []
        original_hook = threading.excepthook
        threading.excepthook = lambda args: thread_errors.append(args.exc_value)
        def emit(event):
            if event.get("event") == "terminal":
                raise OSError("terminal sink unavailable")
            events.append(event)
        executor = self.Executor(backend, emit)
        try:
            executor.submit("terminal-emitter-unavailable", [{"op": "hold_w_until_cancel"}], 1,
                            time.perf_counter_ns() + 10_000_000_000)
            deadline = time.monotonic() + 2
            while backend.admission is None and time.monotonic() < deadline:
                time.sleep(.001)
            self.assertIsNotNone(backend.admission)
            self.assertTrue(executor.cancel("terminal-emitter-unavailable"))
            worker = executor.active[2]
            worker.join(3)
            for watcher in executor.release_watchers:
                watcher.join(3)
            self.assertFalse(worker.is_alive())
            self.assertTrue(any(e.get("event") == "input_released" for e in events))
            self.assertFalse(any(e.get("event") == "terminal" for e in events))
            self.assertIsNotNone(executor.active)
            self.assertEqual(executor.active[0], "terminal-emitter-unavailable")
            self.assertEqual(
                executor.terminal_publication_errors["terminal-emitter-unavailable"]["status"],
                "delivery_unknown")
            with self.assertRaisesRegex(ValueError, "closed or busy"):
                executor.submit("must-not-run", [{"op": "hold_w_until_cancel"}], 1,
                                time.perf_counter_ns() + 10_000_000_000)
            self.assertTrue(any(isinstance(exc, OSError) for exc in thread_errors))
        finally:
            threading.excepthook = original_hook
            executor.close()
            owner.close()

    def test_accept_then_raise_release_delivery_is_not_retried(self):
        SERVER["down"].clear()
        owner = self.InputOwner(None)
        backend = Backend(owner)
        events = []
        accepted_releases = []
        watcher_finished = threading.Event()
        release_all = backend.release_all
        attempts = 0
        def emit(event):
            nonlocal attempts
            if event.get("event") == "input_released":
                attempts += 1
                accepted_releases.append(event)
                if attempts == 1:
                    raise OSError("ack lost after acceptance")
            events.append(event)
        executor = self.Executor(backend, emit)
        publish = executor._publish_release
        def publish_and_signal(identifier, lease):
            try:
                publish(identifier, lease)
            finally:
                watcher_finished.set()
        executor._publish_release = publish_and_signal
        def release_then_wait_for_watcher():
            result = release_all()
            if not watcher_finished.wait(2):
                raise AssertionError("release watcher did not complete before terminal")
            return result
        backend.release_all = release_then_wait_for_watcher
        try:
            executor.submit("release-ack-lost", [{"op": "hold_w_until_cancel"}], 1,
                            time.perf_counter_ns() + 10_000_000_000)
            deadline = time.monotonic() + 2
            while backend.admission is None and time.monotonic() < deadline:
                time.sleep(.001)
            self.assertIsNotNone(backend.admission)
            self.assertTrue(executor.cancel("release-ack-lost"))
            worker = executor.active[2]
            worker.join(3)
            self.assertFalse(worker.is_alive())
            self.assertEqual(attempts, 1)
            self.assertEqual(len(accepted_releases), 1)
            terminal = next(e for e in events if e.get("event") == "terminal")
            self.assertEqual(terminal["input_release_publication"]["status"],
                             "delivery_unknown")
        finally:
            executor.close()
            owner.close()


if __name__ == "__main__":
    unittest.main(verbosity=2)


