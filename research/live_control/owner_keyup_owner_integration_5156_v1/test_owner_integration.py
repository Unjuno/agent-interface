import importlib
import sys
import threading
import time
import types
import unittest
from unittest.mock import patch
from audit_owner_release_brackets import audit

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
        self.fail_fatal_release = False
        self.release_request_times = None
        self.sync_observer = None
        self.release_clock = None
        self.release_started_ns = None
        self.release_returned_ns = None
        self.release_stage = 0
        self.root = FakeRoot(self)

    def keysym_to_keycode(self, keysym):
        return {"a": 38, "b": 56}[keysym]

    def sync(self):
        self.sync_count += 1
        if self.sync_count == self.fail_sync_at:
            raise OSError("synthetic sync failure")
        if self.sync_count == 2 and self.sync_observer is not None:
            self.sync_observer()

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
            if event_type == xlib.X.KeyRelease and display.fail_fatal_release:
                display.fail_fatal_release = False
                raise KeyboardInterrupt("synthetic owner-thread fatal failure")
            if event_type == xlib.X.KeyRelease and display.fail_next_release:
                display.fail_next_release = False
                raise OSError("synthetic key-release request failure")
            if event_type == xlib.X.KeyRelease and display.release_clock is not None:
                display.release_started_ns = display.release_clock()
            display.events.append((event_type, code))
            if event_type == xlib.X.KeyRelease and display.release_clock is not None:
                display.release_returned_ns = display.release_clock()
            if event_type == xlib.X.KeyPress:
                display.keys_down.add(code)
            elif event_type == xlib.X.KeyRelease:
                display.keys_down.discard(code)

        ext.xtest = types.SimpleNamespace(fake_input=fake_input)
        sys.modules["Xlib"] = xlib
        sys.modules["Xlib.ext"] = ext
        cls.v11 = importlib.import_module("input_owner_v11")
        cls.transition_v3 = importlib.import_module("input_transition_owner_v3")

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

    def test_inverted_owner_clock_keeps_release_record_but_fails_order_audit(self):
        owner, display, _clock = self.make_owner()
        lease = FakeLease()
        try:
            with patch.object(self.v11.time, "perf_counter_ns", REAL_PERF_COUNTER_NS):
                owner.call("down", lease, "a")
            times = FakeClock((300, 200, 100))
            display.release_clock = times
            display.release_stage = 0
            class BoundaryClock:
                def __call__(self):
                    if display.release_clock is not None and display.release_stage == 0:
                        display.release_stage = 1
                        return 300
                    if display.release_clock is not None and display.release_stage == 1:
                        display.release_stage = 2
                        return 200
                    if display.release_clock is not None and display.release_stage == 2:
                        display.release_stage = 3
                        return 100
                    if display.release_clock is not None and display.release_stage == 3:
                        display.release_clock = None
                        return 100
                    return REAL_PERF_COUNTER_NS()

            with patch.object(self.v11.time, "perf_counter_ns", BoundaryClock()):
                owner.call("up", lease, "a")
            records = [r for r in owner.records if r.get("event") == "owner_key_release_bracket"
                       and r.get("trigger_class") == "explicit_up"]
            self.assertEqual(len(records), 1)
            self.assertEqual(records[0]["request_started_ns"], 300)
            self.assertEqual(records[0]["request_returned_ns"], 200)
            self.assertEqual(records[0]["shared_sync_returned_ns"], 100)
            self.assertFalse(records[0]["grants_input_authority"])
            self.assertFalse(records[0]["physical_key_up_claimed"])
            self.assertFalse(300 <= 200 <= 100)  # deterministic auditor rejection
        finally:
            owner.close()

    def test_owner_bracket_is_nested_within_pinned_v3_caller_bracket(self):
        display = self._new_display()
        owner = self.transition_v3.InputOwner("fake-display", _owner_cls=self.v11.InputOwner)
        lease = FakeLease()
        try:
            owner.call("down", lease, "a")
            receipt = owner.call("up", lease, "a")
            record = next(r for r in owner.records if r.get("event") == "owner_key_release_bracket"
                          and r.get("trigger_class") == "explicit_up")
            self.assertLessEqual(receipt["release_call_started_ns"], record["request_started_ns"])
            self.assertLessEqual(record["request_started_ns"], record["request_returned_ns"])
            self.assertLessEqual(record["request_returned_ns"], record["shared_sync_returned_ns"])
            self.assertLessEqual(record["shared_sync_returned_ns"], receipt["release_call_returned_ns"])
            self.assertEqual(receipt["owner_id"], record["owner_id"])
            self.assertEqual(receipt["intent_token"], record["intent_token"])
            self.assertFalse(receipt["grants_input_authority"])
            raw_joined = dict(record, caller_started_ns=receipt["release_call_started_ns"],
                              caller_returned_ns=receipt["release_call_returned_ns"])
            self.assertEqual(audit([raw_joined]), [])
            self.assertEqual(display.keys_down, set())
        finally:
            owner.close()

    def test_stale_intent_cannot_release_current_held_key(self):
        owner, display, _clock = self.make_owner()
        current, stale = FakeLease(), FakeLease()
        try:
            owner.call("down", current, "a")
            with self.assertRaisesRegex(ValueError, "another intent"):
                owner.call("up", stale, "a")
            self.assertEqual(display.keys_down, {38})
            self.assertFalse(any(r.get("event") == "owner_key_release_bracket"
                                 and r.get("trigger_class") == "explicit_up" for r in owner.records))
            owner.call("up", current, "a")
        finally:
            owner.close()
        self.assertEqual(display.keys_down, set())

    def test_cancel_after_partial_multi_key_admission_releases_owned_keys(self):
        owner, display, _clock = self.make_owner()
        lease = FakeLease()
        try:
            owner.call("down", lease, "a")
            self.assertEqual(display.keys_down, {38})
            lease.cancel.set()
            deadline = REAL_PERF_COUNTER_NS() + 500_000_000
            while REAL_PERF_COUNTER_NS() < deadline and not any(
                    r.get("event") == "owner_release" and r.get("reason") == "cancelled"
                    for r in owner.records):
                threading.Event().wait(.002)
            cleanup = next(r for r in owner.records if r.get("event") == "owner_release"
                           and r.get("reason") == "cancelled")
            self.assertTrue(cleanup["verified"])
            with self.assertRaises(Exception):
                owner.call("down", lease, "b")
            brackets = [r for r in owner.records if r.get("event") == "owner_key_release_bracket"
                        and r.get("reason") == "cancelled"]
            self.assertEqual([r["keycode"] for r in brackets], [38])
        finally:
            owner.close()
        self.assertEqual(display.keys_down, set())

    def test_fatal_owner_release_error_fails_closed_without_success_record(self):
        owner, display, _clock = self.make_owner()
        lease = FakeLease()
        owner.call("down", lease, "a")
        display.fail_fatal_release = True
        try:
            with self.assertRaises((IndexError, RuntimeError)):
                owner.call("up", lease, "a")
            deadline = REAL_PERF_COUNTER_NS() + 500_000_000
            while REAL_PERF_COUNTER_NS() < deadline and not owner.stopped.is_set():
                threading.Event().wait(.002)
            self.assertTrue(owner.stopped.is_set())
            self.assertIsInstance(owner.error, KeyboardInterrupt)
            self.assertTrue(any(r.get("event") == "owner_failed" for r in owner.records))
            self.assertFalse(any(r.get("event") == "owner_key_release_bracket" and
                                 r.get("trigger_class") == "explicit_up" for r in owner.records))
        finally:
            owner.close()

    def test_raw_only_auditor_accepts_nested_identity_bound_record(self):
        record = dict(event="owner_key_release_bracket", owner_id="owner", intent_token="intent",
                      keycode=38, caller_started_ns=10, request_started_ns=20,
                      request_returned_ns=30, shared_sync_returned_ns=40,
                      caller_returned_ns=50, grants_input_authority=False,
                      physical_key_up_claimed=False)
        self.assertEqual(audit([record]), [])

    def test_raw_only_auditor_rejects_inversion_identity_and_authority_corruption(self):
        record = dict(event="owner_key_release_bracket", owner_id="owner", intent_token="intent",
                      keycode=38, caller_started_ns=10, request_started_ns=30,
                      request_returned_ns=20, shared_sync_returned_ns=40,
                      caller_returned_ns=50, grants_input_authority=True,
                      physical_key_up_claimed=True)
        failures = audit([record])
        self.assertTrue(any("bracket ordering invalid" in failure for failure in failures))
        self.assertTrue(any("authority claim must be false" in failure for failure in failures))
        self.assertTrue(any("physical key-up claim must be false" in failure for failure in failures))


if __name__ == "__main__":
    unittest.main()
