"""Current-main ExecutorV12 expiry composition test; run in a main overlay."""
import sys
import threading
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "research" / "live_control"))

from lease import Expired
import executor_v12
from research.doom.map01_v39_cancel_release_fix_a01_20261005.test_cancel_release import load_candidate


class ExecutorV12ExpiryCompositionTests(unittest.TestCase):
    def test_expiry_publishes_contextual_up_before_verified_terminal(self):
        bridge_test, _hm, harness, _lease, _bm, backend = load_candidate()
        prior_lease_type = executor_v12.Lease

        class ObservedLease(prior_lease_type):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.expected_focus = 42
                self.intent_token = "intent-v13-v12-expiry-a01"

        executor_v12.Lease = ObservedLease
        missing = object()
        parent = bridge_test.Backend.__bases__[0]
        prior_execute = parent.__dict__.get("execute", missing)
        prior_release = parent.__dict__.get("release_all", missing)
        events = []
        admission_seen = threading.Event()
        terminal_seen = threading.Event()

        def emit(row):
            events.append(row)
            if row.get("event") == "input_admission":
                admission_seen.set()
            if row.get("event") == "terminal":
                terminal_seen.set()

        def expire_while_held(self, _step, _cancel, _identifier, _index):
            self.raw("F8", True)
            while time.perf_counter_ns() < self.lease.deadline + 2_000_000:
                time.sleep(0.001)
            raise Expired()

        def release_all(self):
            for key in tuple(self.held):
                self.raw(key, False)
            record = self.owner.call("release", self.lease)
            self._drain_owner_records()
            state = self.owner.call("input_state", self.lease)
            return {"verified": (record.get("verified") is True
                                 and state.get("owned_keycodes") == []
                                 and state.get("owned_buttons") == [])}

        parent.execute = expire_while_held
        parent.release_all = release_all
        backend.sequence = 1
        backend.validate = lambda _steps: None
        backend.emit = emit
        executor = executor_v12.Executor(backend, emit)
        try:
            deadline = time.perf_counter_ns() + 30_000_000
            executor.submit("v13-v12-expiry-a01", [{"op": "hold"}], 1, deadline)
            self.assertTrue(admission_seen.wait(1.0), repr(events))
            self.assertTrue(terminal_seen.wait(1.0), repr(events))
            ups = [e for e in events if e.get("event") == "input_release_measurement"]
            downs = [e for e in events if e.get("event") == "input_admission"]
            terminals = [e for e in events if e.get("event") == "terminal"]
            self.assertEqual(len(ups), 1)
            self.assertEqual(ups[0]["physical_key_measurement"]["classification"],
                             "CONFIRMED_PHYSICAL_UP")
            self.assertEqual(ups[0]["reason"], "expired")
            self.assertEqual((ups[0]["id"], ups[0]["step"]),
                             ("v13-v12-expiry-a01", 0))
            self.assertEqual(ups[0]["intent_token"], "intent-v13-v12-expiry-a01")
            self.assertEqual(ups[0]["physical_key_measurement"]["actuation_id"],
                             downs[0]["physical_key_measurement"]["actuation_id"])
            self.assertEqual(len(terminals), 1)
            self.assertEqual(terminals[0]["status"], "expired")
            self.assertTrue(terminals[0]["release"]["verified"])
            self.assertFalse(backend.lease.cancel.is_set())
            event_names = [e.get("event") for e in events]
            self.assertLess(event_names.index("input_admission"),
                            event_names.index("input_release_measurement"))
            self.assertLess(event_names.index("input_release_measurement"),
                            event_names.index("terminal"))
            self.assertEqual(harness.d.physical, set())
            self.assertEqual(backend.held, set())
        finally:
            executor.close()
            harness.close()
            if prior_execute is missing:
                delattr(parent, "execute")
            else:
                parent.execute = prior_execute
            if prior_release is missing:
                delattr(parent, "release_all")
            else:
                parent.release_all = prior_release
            executor_v12.Lease = prior_lease_type



    def _assert_expiry_release_survives_aggregate_query_failure(self, query_kind):
        config = {"query_fail_on": {5}} if query_kind == "keymap" else None
        bridge_test, hm, harness, _lease, _bm, backend = load_candidate(config)
        prior_lease_type = executor_v12.Lease

        class ObservedLease(prior_lease_type):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.expected_focus = 42
                self.intent_token = "intent-v13-v12-query-failure"

        executor_v12.Lease = ObservedLease
        missing = object()
        parent = bridge_test.Backend.__bases__[0]
        prior_execute = parent.__dict__.get("execute", missing)
        prior_release = parent.__dict__.get("release_all", missing)
        events = []
        terminal_seen = threading.Event()
        pointer_calls = []
        real_query_pointer = hm.Root.query_pointer

        if query_kind == "pointer":
            def fail_first_pointer_query(root):
                pointer_calls.append("query_pointer")
                if len(pointer_calls) == 1:
                    raise RuntimeError("injected aggregate pointer query failure")
                return real_query_pointer(root)
            hm.Root.query_pointer = fail_first_pointer_query

        def emit(row):
            events.append(row)
            if row.get("event") == "terminal":
                terminal_seen.set()

        def expire_after_owner_cleanup(self, _step, _cancel, _identifier, _index):
            self.raw("F8", True)
            until = time.monotonic() + 1.0
            while time.perf_counter_ns() < self.lease.deadline + 2_000_000:
                if time.monotonic() >= until:
                    raise AssertionError("lease did not expire")
                time.sleep(0.001)
            while 74 in harness.d.physical:
                if time.monotonic() >= until:
                    raise AssertionError("owner did not release F8 after expiry")
                time.sleep(0.001)
            raise Expired()

        def release_all(self):
            for key in tuple(self.held):
                self.raw(key, False)
            record = self.owner.call("release", self.lease)
            self._drain_owner_records()
            state = self.owner.call("input_state", self.lease)
            return {"verified": (record.get("verified") is True
                                 and state.get("owned_keycodes") == []
                                 and state.get("owned_buttons") == [])}

        parent.execute = expire_after_owner_cleanup
        parent.release_all = release_all
        backend.sequence = 1
        backend.validate = lambda _steps: None
        backend.emit = emit
        executor = executor_v12.Executor(backend, emit)
        try:
            deadline = time.perf_counter_ns() + 30_000_000
            executor.submit("v13-v12-query-failure", [{"op": "hold"}], 1, deadline)
            self.assertTrue(terminal_seen.wait(1.5), repr(events))
            expired_ups = [e for e in events
                           if e.get("event") == "input_release_measurement"
                           and e.get("reason") == "expired"]
            self.assertEqual(len(expired_ups), 1)
            self.assertEqual(expired_ups[0]["physical_key_measurement"]["classification"],
                             "CONFIRMED_PHYSICAL_UP")
            self.assertEqual((expired_ups[0]["id"], expired_ups[0]["step"]),
                             ("v13-v12-query-failure", 0))
            partial = [r for r in harness.owner.records
                       if r.get("event") == "owner_release" and r.get("verified") is False]
            self.assertEqual(len(partial), 1)
            self.assertNotIn("keys_down", partial[0])
            terminals = [e for e in events if e.get("event") == "terminal"]
            self.assertEqual(len(terminals), 1)
            self.assertEqual(terminals[0]["status"], "expired")
            self.assertTrue(terminals[0]["release"]["verified"])
            self.assertEqual(harness.d.physical, set())
            self.assertEqual(backend.held, set())
            if query_kind == "pointer":
                self.assertGreaterEqual(len(pointer_calls), 2)
            else:
                self.assertGreaterEqual(harness.d.query_i, 5)
        finally:
            executor.close()
            harness.close()
            if query_kind == "pointer":
                hm.Root.query_pointer = real_query_pointer
            if prior_execute is missing:
                delattr(parent, "execute")
            else:
                parent.execute = prior_execute
            if prior_release is missing:
                delattr(parent, "release_all")
            else:
                parent.release_all = prior_release
            executor_v12.Lease = prior_lease_type

    def test_v12_expiry_retains_keyup_when_owner_pointer_query_fails(self):
        self._assert_expiry_release_survives_aggregate_query_failure("pointer")

    def test_v12_expiry_retains_keyup_when_owner_keymap_query_fails(self):
        self._assert_expiry_release_survives_aggregate_query_failure("keymap")


if __name__ == "__main__":
    unittest.main(verbosity=2)
