"""Execute the v10 owner release handler under a forced cancellation interleaving."""
import importlib.util
import os
from pathlib import Path
import queue
import sys
import threading
import time
import types
import unittest

ROOT = Path(__file__).resolve().parents[4]
LIVE = ROOT / "research" / "live_control"
OWNER_PATH = Path(os.environ.get("OWNER_UNDER_TEST", LIVE / "input_owner_v10.py"))


class FakeDisplay:
    def __init__(self, _name):
        self.down = set()
        self.events = []
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
        return None


class Lease:
    def __init__(self):
        self.deadline = time.perf_counter_ns() + 5_000_000_000
        self.cancel = threading.Event()
        self.expected_focus = 41
        self.focus_invalid = False
        self.interruptions = []

    def check(self):
        if time.perf_counter_ns() >= self.deadline:
            raise RuntimeError("fixture lease unexpectedly expired")

    def record_interruption(self, receipt):
        self.interruptions.append(receipt)


def load_owner(dequeued):
    saved = {name: sys.modules.get(name) for name in (
        "Xlib", "Xlib.X", "Xlib.XK", "Xlib.display", "Xlib.error",
        "Xlib.ext", "Xlib.ext.xtest", "executor_v3")}
    xlib = types.ModuleType("Xlib")
    constants = types.SimpleNamespace(KeyPress=2, KeyRelease=3, ButtonRelease=5,
                                      Button1Mask=256, AnyPropertyType=0)
    xlib.X = constants
    xk = types.ModuleType("Xlib.XK")
    xk.string_to_keysym = lambda _key: 1
    display = types.ModuleType("Xlib.display")
    displays = []

    def make_display(name):
        instance = FakeDisplay(name)
        displays.append(instance)
        return instance

    display.Display = make_display
    error = types.ModuleType("Xlib.error")
    error.BadWindow = type("BadWindow", (Exception,), {})
    error.BadDrawable = type("BadDrawable", (Exception,), {})
    ext = types.ModuleType("Xlib.ext")
    xtest = types.ModuleType("Xlib.ext.xtest")

    def fake_input(connection, event, code):
        connection.events.append((event, code))
        if event == constants.KeyPress:
            connection.down.add(code)
        elif event == constants.KeyRelease:
            connection.down.discard(code)

    xtest.fake_input = fake_input
    ext.xtest = xtest
    xlib.XK, xlib.display, xlib.error, xlib.ext = xk, display, error, ext
    executor = types.ModuleType("executor_v3")
    executor.Cancelled = type("Cancelled", (Exception,), {})
    executor.DecisionRequired = type("DecisionRequired", (Exception,), {})
    sys.modules.update({
        "Xlib": xlib, "Xlib.X": types.ModuleType("Xlib.X"), "Xlib.XK": xk,
        "Xlib.display": display, "Xlib.error": error, "Xlib.ext": ext,
        "Xlib.ext.xtest": xtest, "executor_v3": executor,
    })
    owner_spec = importlib.util.spec_from_file_location("owner_under_test", OWNER_PATH)
    owner = importlib.util.module_from_spec(owner_spec)
    sys.modules["owner_under_test"] = owner
    owner_spec.loader.exec_module(owner)

    factory = queue.Queue

    def controlled_queue(*args, **kwargs):
        result = factory(*args, **kwargs)
        original_get = result.get

        def get(*get_args, **get_kwargs):
            item = original_get(*get_args, **get_kwargs)
            if item[0] == "release":
                dequeued.set()
                # This occurs after the owner-loop cancellation precheck and
                # after the request is dequeued, but before release dispatch.
                owner_lease[0].cancel.set()
            return item

        result.get = get
        return result

    owner_lease = [None]
    queue.Queue = controlled_queue
    try:
        instance = owner.InputOwner(":fake")
    finally:
        queue.Queue = factory
    return instance, displays, constants, owner_lease, saved


def restore_modules(saved):
    sys.modules.pop("owner_under_test", None)
    for name, module in saved.items():
        if module is None:
            sys.modules.pop(name, None)
        else:
            sys.modules[name] = module


class CancellationReleaseCauseTests(unittest.TestCase):
    def _exercise(self, cancel_after_dequeue):
        dequeued = threading.Event()
        owner, displays, constants, lease_slot, saved = load_owner(dequeued)
        lease = Lease()
        lease_slot[0] = lease
        try:
            owner.call("down", lease, "W")
            if not cancel_after_dequeue:
                # Keep the request queue hook from changing state on this path.
                lease.cancel.set = lambda: None
            receipt = owner.call("release", lease)
            self.assertTrue(dequeued.wait(1))
            self.assertTrue(receipt["verified"])
            self.assertEqual(displays[0].events,
                             [(constants.KeyPress, 38), (constants.KeyRelease, 38)])
            self.assertEqual(len(lease.interruptions), 1)
            return lease.interruptions[0]["reason"]
        finally:
            owner.close()
            restore_modules(saved)

    def test_cancel_arriving_after_dequeue_is_preserved_as_release_cause(self):
        self.assertEqual(self._exercise(True), "cancelled")

    def test_ordinary_release_remains_ordinary(self):
        self.assertEqual(self._exercise(False), "release")


if __name__ == "__main__":
    unittest.main(verbosity=2)

