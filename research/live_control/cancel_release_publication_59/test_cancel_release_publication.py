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
        try:
            executor.submit("cancel-release-test", [{"op": "hold_w_until_cancel"}], 1,
                            time.perf_counter_ns() + 10_000_000_000)
            deadline = time.monotonic() + 2
            while backend.admission is None and time.monotonic() < deadline:
                time.sleep(.001)
            self.assertIsNotNone(backend.admission)
            self.assertEqual(backend.admission["event"], "input_admission")
            self.assertTrue(executor.cancel("cancel-release-test"))
            worker = executor.active[2]
            worker.join(3)
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
            executor.close()
            owner.close()


if __name__ == "__main__":
    unittest.main(verbosity=2)

