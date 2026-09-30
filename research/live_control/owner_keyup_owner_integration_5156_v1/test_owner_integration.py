import importlib
import sys
import threading
import time
import types
import unittest
from unittest.mock import patch

REAL_PERF_COUNTER_NS = time.perf_counter_ns


class FakeRoot:
    id = 1

    def __init__(self, display):
        self.display = display

    def query_pointer(self):
        return types.SimpleNamespace(mask=0, root_x=0, root_y=0)


class FakeDisplay:
    def __init__(self):
        self.events = []
        self.keys_down = set()
        self.sync_count = 0
        self.fail_sync_at = None
        self.fail_next_release = False
        self.root = FakeRoot(self)

    def keysym_to_keycode(self, keysym):
        return {"a": 38, "b": 56}[keysym]

    def sync(self):
        self.sync_count += 1
        if self.sync_count == self.fail_sync_at:
            raise OSError("synthetic sync failure")

    def get_input_focus(self):
        return types.SimpleNamespace(focus=17)

    def screen(self):
        return types.SimpleNamespace(root=self.root)

    def query_keymap(self):
        bitmap = bytearray(32)
        for code in self.keys_down:
            bitmap[code // 8] |= 1 << (code % 8)
        return bitmap

    def close(self):
        pass


class FakeLease:
    def __init__(self):
        self.deadline = time.perf_counter_ns() + 20_000_000_000
        self.cancel = threading.Event()
        self.expected_focus = 17
        self.intent_token = "intent-test"
        self.focus_invalid = False

    def check(self):
        if time.perf_counter_ns() >= self.deadline:
            raise RuntimeError("synthetic lease expired")


class FakeClock:
    def __init__(self, values):
        self.values = iter(values)

    def __call__(self):
        try:
            return next(self.values)
        except StopIteration:
            return REAL_PERF_COUNTER_NS()


class OwnerIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.displays = []
        xlib = types.ModuleType("Xlib")
        xlib.__path__ = []
        xlib.X = types.SimpleNamespace(
            KeyPress=2, KeyRelease=3, ButtonRelease=5, Button1Mask=256,
            AnyPropertyType=0, IsViewable=2,
        )
        xlib.XK = types.SimpleNamespace(string_to_keysym=lambda value: value)
        xlib.display = types.SimpleNamespace(
            Display=lambda _name: cls._new_display()
        )
        xlib.error = types.SimpleNamespace(BadWindow=type("BadWindow", (Exception,), {}),
                                           BadDrawable=type("BadDrawable", (Exception,), {}))
        ext = types.ModuleType("Xlib.ext")

        def fake_input(display, event_type, code, **_kwargs):
            if event_type == xlib.X.KeyRelease and display.fail_next_release:
                display.fail_next_release = False
                raise OSError("synthetic key-release request failure")
            display.events.append((event_type, code))
            if event_type == xlib.X.KeyPress:
                display.keys_down.add(code)
            elif event_type == xlib.X.KeyRelease:
                display.keys_down.discard(code)

        ext.xtest = types.SimpleNamespace(fake_input=fake_input)
        sys.modules["Xlib"] = xlib
        sys.modules["Xlib.ext"] = ext
        cls.v11 = importlib.import_module("input_owner_v11")

    @classmethod
    def _new_display(cls):
        instance = FakeDisplay()
        cls.displays.append(instance)
        return instance

    def make_owner(self, clock_values=(100, 110, 120)):
        clock = FakeClock(clock_values)
        with patch.object(self.v11.time, "perf_counter_ns", clock):
            owner = self.v11.InputOwner("fake-display")
        return owner, self.displays[-1], clock

    def test_explicit_up_emits_owner_request_and_sync_bracket(self):
        owner, display, clock = self.make_owner()
        lease = FakeLease()
        explicit_up_clock = FakeClock((100, 110, 120))
        try:
            with patch.object(self.v11.time, "perf_counter_ns", clock):
                owner.call("down", lease, "a")
            with patch.object(self.v11.time, "perf_counter_ns", explicit_up_clock):
                owner.call("up", lease, "a")
            with patch.object(self.v11.time, "perf_counter_ns", REAL_PERF_COUNTER_NS):
                owner.close()
        finally:
            if not owner.closed:
                owner.close()

        records = [r for r in owner.records if r.get("event") == "owner_key_release_bracket"]
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["owner_id"], owner.owner_id)
        self.assertEqual(records[0]["intent_token"], lease.intent_token)
        self.assertEqual(records[0]["trigger_class"], "explicit_up")
        self.assertEqual(records[0]["reason"], "explicit_up")
        self.assertEqual(records[0]["key"], "a")
        self.assertEqual(records[0]["keycode"], 38)
        self.assertEqual(records[0]["request_started_ns"], 100)
        self.assertEqual(records[0]["request_returned_ns"], 110)
        self.assertEqual(records[0]["shared_sync_returned_ns"], 120)
        self.assertFalse(records[0]["physical_key_up_claimed"])
        self.assertFalse(records[0]["grants_input_authority"])
        self.assertEqual(display.keys_down, set())
        self.assertEqual(display.sync_count, 3)

    def test_aggregate_cleanup_records_each_key_after_one_shared_sync(self):
        owner, display, clock = self.make_owner()
        lease = FakeLease()
        try:
            with patch.object(self.v11.time, "perf_counter_ns", REAL_PERF_COUNTER_NS):
                owner.call("down", lease, "a")
                owner.call("down", lease, "b")
                owner.call("release", lease)
                owner.close()
        finally:
            if not owner.closed:
                owner.close()

        records = [r for r in owner.records if r.get("event") == "owner_key_release_bracket"]
        self.assertEqual([r["key"] for r in records], [None, None])
        self.assertEqual([r["keycode"] for r in records], [38, 56])
        self.assertTrue(all(r["trigger_class"] == "owner_lease_cleanup" for r in records))
        self.assertTrue(all(r["reason"] == "release" for r in records))
        self.assertEqual(records[0]["shared_sync_returned_ns"], records[1]["shared_sync_returned_ns"])
        self.assertEqual(display.sync_count, 4)  # two presses, batched release, existing close cleanup
        self.assertEqual(display.keys_down, set())

    def test_explicit_up_request_failure_emits_no_success_bracket(self):
        owner, display, clock = self.make_owner()
        lease = FakeLease()
        try:
            with patch.object(self.v11.time, "perf_counter_ns", REAL_PERF_COUNTER_NS):
                owner.call("down", lease, "a")
                display.fail_next_release = True
                with self.assertRaisesRegex(OSError, "key-release request failure"):
                    owner.call("up", lease, "a")
        finally:
            owner.close()
        self.assertFalse(any(r.get("event") == "owner_key_release_bracket" and
                             r.get("trigger_class") == "explicit_up" for r in owner.records))
        self.assertEqual(display.keys_down, set())

    def test_explicit_up_sync_failure_emits_no_success_bracket(self):
        owner, display, clock = self.make_owner()
        lease = FakeLease()
        try:
            with patch.object(self.v11.time, "perf_counter_ns", REAL_PERF_COUNTER_NS):
                owner.call("down", lease, "a")
                display.fail_sync_at = 2
                with self.assertRaisesRegex(OSError, "sync failure"):
                    owner.call("up", lease, "a")
        finally:
            owner.close()
        self.assertFalse(any(r.get("event") == "owner_key_release_bracket" and
                             r.get("trigger_class") == "explicit_up" for r in owner.records))
        self.assertEqual(display.keys_down, set())


if __name__ == "__main__":
    unittest.main()
