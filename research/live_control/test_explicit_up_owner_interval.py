"""Owner-thread timing regression for V11 explicit key-up receipts.

Fake Xlib only: timings bound an XTest KeyRelease request through the existing
owner-thread XSync. They do not measure hardware state or application use.
"""
import sys
import threading
import time
import types
import unittest

SERVER = {"down": set(), "events": [], "lock": threading.Lock()}

class FakeRoot:
    def query_pointer(self):
        return types.SimpleNamespace(mask=0)

class FakeDisplay:
    def __init__(self, _name=None):
        self.events = []
        self.root = FakeRoot()
    def get_input_focus(self):
        return types.SimpleNamespace(focus=42)
    def screen(self):
        return types.SimpleNamespace(root=self.root)
    def query_keymap(self):
        return bytes(32)
    def keysym_to_keycode(self, sym):
        return sym + 10
    def sync(self):
        if self.events and self.events[-1]["kind"] == "release_request":
            self.events[-1]["sync_completed_ns"] = time.perf_counter_ns()
    def close(self):
        pass

def fake_input(display, event, code, **_kwargs):
    if event == 2:
        with SERVER["lock"]:
            SERVER["down"].add(code)
        display.events.append({"kind": "press", "code": code})
    elif event == 3:
        event_record = {
            "kind": "release_request",
            "code": code,
            "request_seen_ns": time.perf_counter_ns(),
        }
        with SERVER["lock"]:
            SERVER["down"].discard(code)
        display.events.append(event_record)
        SERVER["events"].append(event_record)
    else:
        raise AssertionError("unexpected fake X event: %r" % event)

xlib = types.ModuleType("Xlib")
xlib.__path__ = []
xlib.X = types.SimpleNamespace(
    KeyPress=2, KeyRelease=3, ButtonRelease=5, ButtonPress=4,
    Button1Mask=1, AnyPropertyType=0, IsViewable=2, MotionNotify=6,
)
xlib.XK = types.SimpleNamespace(string_to_keysym=lambda value: ord(value[0]))
xlib.display = types.SimpleNamespace(Display=FakeDisplay)
xlib.error = types.SimpleNamespace(
    BadWindow=type("BadWindow", (Exception,), {}),
    BadDrawable=type("BadDrawable", (Exception,), {}),
)
ext = types.ModuleType("Xlib.ext")
ext.__path__ = []
xtest = types.ModuleType("Xlib.ext.xtest")
xtest.fake_input = fake_input
ext.xtest = xtest
xlib.ext = ext
sys.modules.update({"Xlib": xlib, "Xlib.ext": ext, "Xlib.ext.xtest": xtest})

from input_owner_v10 import InputOwner as V10
from input_owner_v11 import InputOwner as V11

# If the contract-only test module imported the V10 module first, replace its
# import-only globals with these fake runtime implementations.
import input_owner_v10
input_owner_v10.X = xlib.X
input_owner_v10.XK = xlib.XK
input_owner_v10.display = xlib.display
input_owner_v10.error = xlib.error
input_owner_v10.xtest = xtest

class Lease:
    deadline = time.perf_counter_ns() + 5_000_000_000
    intent_token = "test-intent"
    expected_focus = 42
    def __init__(self):
        self.cancel = threading.Event()
    def check(self):
        if self.cancel.is_set():
            raise RuntimeError("cancelled")
        if time.perf_counter_ns() >= self.deadline:
            raise TimeoutError("expired")

class ExplicitUpOwnerIntervalTests(unittest.TestCase):
    def setUp(self):
        with SERVER["lock"]:
            SERVER["down"].clear()
            SERVER["events"].clear()

    def test_explicit_up_receipt_has_nested_owner_thread_interval(self):
        owner = V11(":fake")
        lease = Lease()
        try:
            admitted = owner.call("down", lease, "W")
            self.assertEqual(admitted["event"], "input_admission")
            receipt = owner.call("up", lease, "W")
            self.assertEqual(receipt["event"], "input_release_rpc")
            self.assertEqual(receipt["payload"], "W")
            self.assertEqual(receipt["intent_token"], lease.intent_token)
            caller_start, caller_end = receipt["release_transition_interval_ns"]
            owner_start, owner_end = receipt["owner_thread_release_interval_ns"]
            self.assertLessEqual(caller_start, owner_start)
            self.assertLessEqual(owner_start, owner_end)
            self.assertLessEqual(owner_end, caller_end)
            event = SERVER["events"][-1]
            self.assertEqual(event["code"], ord("W") + 10)
            self.assertLessEqual(owner_start, event["request_seen_ns"])
            self.assertLessEqual(event["request_seen_ns"], event["sync_completed_ns"])
            self.assertLessEqual(event["sync_completed_ns"], owner_end)
            self.assertFalse(receipt["application_consumption_observed"])
            self.assertFalse(receipt["grants_input_authority"])
            self.assertEqual(SERVER["down"], set())
        finally:
            owner.close()

    def test_unmeasured_v10_up_keeps_none_return_contract(self):
        owner = V10(":fake")
        try:
            self.assertIsNone(owner.call("up", Lease(), "W"))
        finally:
            owner.close()

if __name__ == "__main__":
    unittest.main(verbosity=2)

