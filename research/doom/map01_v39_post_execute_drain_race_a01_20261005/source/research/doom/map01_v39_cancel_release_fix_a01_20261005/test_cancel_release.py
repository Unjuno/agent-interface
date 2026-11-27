import importlib.util
import sys
import threading
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
DOOM = ROOT / "research" / "doom"
FIX_PATH = DOOM / "map01_v39_cancel_release_fix_a01_20261005"
BRIDGE_TEST_PATH = DOOM / "map01_v39_perkey_bridge_a01" / "test_bridge.py"
OWNER_V13_PATH = FIX_PATH / "input_owner_v13_candidate.py"
BRIDGE_V2_PATH = FIX_PATH / "bridge_v2_candidate.py"


def load_candidate(config=None):
    spec = importlib.util.spec_from_file_location("bridge_test_for_cancel_fix", BRIDGE_TEST_PATH)
    bridge_test = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = bridge_test
    assert spec.loader is not None
    spec.loader.exec_module(bridge_test)
    harness_module = bridge_test.load_v12_test_harness()
    owner_module = harness_module.load("input_owner_v13_candidate", OWNER_V13_PATH)
    sys.path.insert(0, str(FIX_PATH))
    spec = importlib.util.spec_from_file_location("bridge_v2_candidate", BRIDGE_V2_PATH)
    bridge_module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = bridge_module
    assert spec.loader is not None
    spec.loader.exec_module(bridge_module)
    harness = harness_module.Harness(owner_module, config)
    lease = harness_module.Lease(intent="intent-cancel-fix")
    backend = object.__new__(bridge_module.Backend)
    backend.owner = harness.owner
    backend.lease = lease
    backend.held = set()
    backend._input_event_context = None
    backend._owner_record_cursor = 0
    backend.events = []
    backend.emit = backend.events.append
    return bridge_test, harness_module, harness, lease, bridge_module, backend


def run_program(bridge_test, backend, lease, program, identifier="cover-cancel-fix", step=4):
    previous = bridge_test.Backend.__bases__[0]
    missing = object()
    prior = previous.__dict__.get("execute", missing)

    def execute(self, _step, _cancel, _identifier, _index):
        return program(self, identifier, step)

    previous.execute = execute
    try:
        return backend.execute({}, lease.cancel, identifier, step)
    finally:
        if prior is missing:
            delattr(previous, "execute")
        else:
            previous.execute = prior


def one_key_cancel(self, _identifier, _step):
    self.raw("F8", True)
    self.lease.cancel.set()


class CancellationReceiptTests(unittest.TestCase):
    def test_cancel_cleanup_emits_up_receipt_joined_to_admission_context(self):
        bridge_test, _hm, harness, lease, _bm, backend = load_candidate()
        try:
            run_program(bridge_test, backend, lease, one_key_cancel)
            down = next(row for row in backend.events if row.get("event") == "input_admission")
            up_rows = [row for row in backend.events
                       if row.get("event") == "input_release_measurement"]
            self.assertEqual(len(up_rows), 1)
            up = up_rows[0]
            self.assertEqual((up.get("id"), up.get("step")), ("cover-cancel-fix", 4))
            self.assertEqual(up["physical_key_measurement"]["actuation_id"],
                             down["physical_key_measurement"]["actuation_id"])
            self.assertEqual(up["physical_key_measurement"]["classification"],
                             "CONFIRMED_PHYSICAL_UP")
            measurement = up["physical_key_measurement"]
            self.assertEqual(measurement["identity_status"], "RETIRED")
            self.assertEqual(up["reason"], "cancelled")
            self.assertEqual(measurement["adapter_edge"]["edge"], "up")
            self.assertFalse(measurement["adapter_edge"]["grants_input_authority"])
            interval = measurement["adapter_edge"]["interval"]
            self.assertEqual(interval, [measurement["pre_sample"]["finished_ns"],
                                        measurement["post_sample"]["finished_ns"]])
            self.assertLessEqual(measurement["pre_sample"]["finished_ns"],
                                 measurement["release_request_ns"])
            self.assertLessEqual(measurement["release_request_ns"],
                                 measurement["sync_return_ns"])
            self.assertLessEqual(measurement["sync_return_ns"],
                                 measurement["post_sample"]["started_ns"])
        finally:
            harness.close()

    def test_verified_async_cleanup_reconciles_bridge_held_state(self):
        bridge_test, _hm, harness, lease, _bm, backend = load_candidate()
        try:
            run_program(bridge_test, backend, lease, one_key_cancel)
            self.assertEqual(harness.d.physical, set())
            self.assertEqual(backend.held, set())
        finally:
            harness.close()

    def test_each_cancelled_key_keeps_its_own_admission_context(self):
        bridge_test, hm, harness, lease, _bm, backend = load_candidate()
        hm.owner_module.XK.string_to_keysym = lambda key: {"F8": 8, "F9": 9}[key]
        harness.d.keysym_to_keycode = lambda sym: {8: 74, 9: 75}[sym]

        def two_key_cancel(self, identifier, step):
            self._input_event_context = (identifier, step)
            self.raw("F8", True)
            self._input_event_context = (identifier, step + 1)
            self.raw("F9", True)
            lease.cancel.set()

        try:
            run_program(bridge_test, backend, lease, two_key_cancel, step=10)
            downs = {row["key"]: row for row in backend.events
                     if row.get("event") == "input_admission"}
            ups = {row["key"]: row for row in backend.events
                   if row.get("event") == "input_release_measurement"}
            self.assertEqual(set(ups), {"F8", "F9"})
            self.assertEqual(ups["F8"]["step"], 10)
            self.assertEqual(ups["F9"]["step"], 11)
            self.assertNotEqual(ups["F8"]["physical_key_measurement"]["actuation_id"],
                                ups["F9"]["physical_key_measurement"]["actuation_id"])
            for key in ("F8", "F9"):
                self.assertEqual(ups[key]["id"], "cover-cancel-fix")
                self.assertEqual(ups[key]["physical_key_measurement"]["actuation_id"],
                                 downs[key]["physical_key_measurement"]["actuation_id"])
            self.assertEqual(harness.d.physical, set())
            self.assertEqual(backend.held, set())
        finally:
            harness.close()

    def test_ordinary_up_still_emits_one_matching_receipt(self):
        _bt, _hm, harness, lease, _bm, backend = load_candidate()
        try:
            backend._input_event_context = ("ordinary-program", 2)
            backend.raw("F8", True)
            backend._input_event_context = ("ordinary-program", 3)
            backend.raw("F8", False)
            rows = [row for row in backend.events
                    if row.get("event") in {"input_admission", "input_release_measurement"}]
            self.assertEqual([row["event"] for row in rows],
                             ["input_admission", "input_release_measurement"])
            self.assertEqual(rows[0]["physical_key_measurement"]["actuation_id"],
                             rows[1]["physical_key_measurement"]["actuation_id"])
            self.assertEqual(rows[1]["step"], 3)
            self.assertEqual(backend.held, set())
            self.assertEqual(harness.d.physical, set())
        finally:
            harness.close()

    def test_unavailable_per_key_samples_never_claim_confirmed_up(self):
        bridge_test, _hm, harness, lease, _bm, backend = load_candidate({"query_fail_on": {4}})
        try:
            run_program(bridge_test, backend, lease, one_key_cancel)
            ups = [row for row in backend.events
                   if row.get("event") == "input_release_measurement"]
            self.assertEqual(len(ups), 1)
            measurement = ups[0]["physical_key_measurement"]
            self.assertEqual(measurement["classification"], "PHYSICAL_SAMPLE_UNAVAILABLE")
            self.assertIsNone(measurement["adapter_edge"])
            self.assertEqual(harness.d.physical, set())
            self.assertEqual(backend.held, set())
        finally:
            harness.close()

    def test_reconciliation_error_does_not_drop_recorded_release_receipt(self):
        bridge_test, _hm, harness, lease, _bm, backend = load_candidate()
        real_call = harness.owner.call

        def fail_reconciliation(operation, *args, **kwargs):
            if operation == "input_state":
                deadline = time.monotonic() + 1.0
                while not any(row.get("event") == "owner_release"
                              for row in harness.owner.records):
                    if time.monotonic() >= deadline:
                        raise AssertionError("owner cleanup did not record before reconciliation")
                    time.sleep(0.001)
                raise RuntimeError("injected reconciliation failure")
            return real_call(operation, *args, **kwargs)

        harness.owner.call = fail_reconciliation
        try:
            with self.assertRaisesRegex(RuntimeError, "injected reconciliation failure"):
                run_program(bridge_test, backend, lease, one_key_cancel)
            ups = [row for row in backend.events
                   if row.get("event") == "input_release_measurement"]
            self.assertEqual(len(ups), 1)
            self.assertEqual(ups[0]["physical_key_measurement"]["classification"],
                             "CONFIRMED_PHYSICAL_UP")
            self.assertEqual(backend.held, set())
            self.assertEqual(harness.d.physical, set())
        finally:
            harness.close()

    def test_expired_program_exit_drains_owner_cleanup_without_cancel_event(self):
        bridge_test, _hm, harness, lease, _bm, backend = load_candidate()
        real_call = harness.owner.call
        state_queries = []

        def track_state_query(operation, *args, **kwargs):
            if operation == "input_state":
                state_queries.append(operation)
            return real_call(operation, *args, **kwargs)

        harness.owner.call = track_state_query

        def expire_after_cleanup(self, identifier, step):
            self._input_event_context = (identifier, step)
            self.raw("F8", True)
            self.owner.call("release", self.lease)
            raise RuntimeError("Expired")

        try:
            with self.assertRaisesRegex(RuntimeError, "Expired"):
                run_program(bridge_test, backend, lease, expire_after_cleanup,
                            identifier="expired-cleanup", step=8)
            ups = [row for row in backend.events
                   if row.get("event") == "input_release_measurement"]
            self.assertEqual(len(ups), 1)
            self.assertEqual((ups[0]["id"], ups[0]["step"]),
                             ("expired-cleanup", 8))
            self.assertEqual(ups[0]["physical_key_measurement"]["classification"],
                             "CONFIRMED_PHYSICAL_UP")
            self.assertFalse(lease.cancel.is_set())
            self.assertEqual(state_queries, [])
            self.assertEqual(backend.held, set())
            self.assertEqual(harness.d.physical, set())
        finally:
            harness.close()


    def test_executor_cancel_terminal_contains_one_verified_cleanup_receipt(self):
        bridge_test, _hm, harness, _lease, _bm, backend = load_candidate()
        import executor_v3
        Cancelled, Executor = executor_v3.Cancelled, executor_v3.Executor
        parent = bridge_test.Backend.__bases__[0]
        prior_lease_type = executor_v3.Lease

        class ObservedLease(prior_lease_type):
            def __init__(self, deadline):
                super().__init__(deadline)
                self.expected_focus = 42
                self.intent_token = "intent-cancel-executor-a01"

        executor_v3.Lease = ObservedLease
        missing = object()
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

        def blocking_program(self, _step, cancel, _identifier, _index):
            self.raw("F8", True)
            cancel.wait(2.0)
            raise Cancelled()

        def release_all(self):
            for key in list(self.held):
                self.raw(key, False)
            state = self.owner.call("input_state", self.lease)
            return {"verified": (self.held == set()
                                 and state.get("owned_keycodes") == []
                                 and state.get("owned_buttons") == [])}

        parent.execute = blocking_program
        parent.release_all = release_all
        backend.sequence = 1
        backend.validate = lambda _steps: None
        backend.emit = emit
        executor = Executor(backend, emit)
        try:
            executor.submit("cancel-executor-a01", [{"op": "hold"}], 1,
                            time.perf_counter_ns() + 10_000_000_000)
            self.assertTrue(admission_seen.wait(1.0), repr(events))
            self.assertTrue(executor.cancel("cancel-executor-a01"))
            self.assertTrue(terminal_seen.wait(1.0))
            ups = [row for row in events if row.get("event") == "input_release_measurement"]
            terminals = [row for row in events if row.get("event") == "terminal"]
            self.assertEqual(len(ups), 1)
            self.assertEqual(ups[0]["physical_key_measurement"]["classification"],
                             "CONFIRMED_PHYSICAL_UP")
            self.assertEqual((ups[0]["id"], ups[0]["step"]),
                             ("cancel-executor-a01", 0))
            self.assertEqual(len(terminals), 1)
            self.assertEqual(terminals[0]["status"], "cancelled")
            self.assertTrue(terminals[0]["release"]["verified"])
            event_names = [row.get("event") for row in events]
            self.assertLess(event_names.index("input_admission"),
                            event_names.index("cancel_requested"))
            self.assertLess(event_names.index("cancel_requested"),
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
            executor_v3.Lease = prior_lease_type

    def test_executor_expiry_terminal_contains_one_verified_cleanup_receipt(self):
        bridge_test, _hm, harness, _lease, _bm, backend = load_candidate()
        import executor_v3
        from lease import Expired
        Executor = executor_v3.Executor
        prior_lease_type = executor_v3.Lease

        class ObservedLease(prior_lease_type):
            def __init__(self, deadline):
                super().__init__(deadline)
                self.expected_focus = 42
                self.intent_token = "intent-expiry-executor-a01"

        executor_v3.Lease = ObservedLease
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

        def expiry_program(self, _step, _cancel, _identifier, _index):
            self.raw("F8", True)
            while time.perf_counter_ns() < self.lease.deadline + 2_000_000:
                time.sleep(0.001)
            raise Expired()

        def release_all(self):
            state = self.owner.call("input_state", self.lease)
            return {"verified": (state.get("owned_keycodes") == []
                                 and state.get("owned_buttons") == [])}

        parent.execute = expiry_program
        parent.release_all = release_all
        backend.sequence = 1
        backend.validate = lambda _steps: None
        backend.emit = emit
        executor = Executor(backend, emit)
        try:
            deadline = time.perf_counter_ns() + 30_000_000
            executor.submit("expiry-executor-a01", [{"op": "hold"}], 1, deadline)
            self.assertTrue(admission_seen.wait(1.0), repr(events))
            self.assertTrue(terminal_seen.wait(1.0), repr(events))
            ups = [row for row in events if row.get("event") == "input_release_measurement"]
            terminals = [row for row in events if row.get("event") == "terminal"]
            downs = [row for row in events if row.get("event") == "input_admission"]
            self.assertEqual(len(ups), 1)
            self.assertEqual(ups[0]["physical_key_measurement"]["classification"],
                             "CONFIRMED_PHYSICAL_UP")
            self.assertEqual(ups[0]["reason"], "expired")
            self.assertEqual((ups[0]["id"], ups[0]["step"]),
                             ("expiry-executor-a01", 0))
            self.assertEqual(ups[0]["physical_key_measurement"]["actuation_id"],
                             downs[0]["physical_key_measurement"]["actuation_id"])
            self.assertEqual(len(terminals), 1)
            self.assertEqual(terminals[0]["status"], "expired")
            self.assertTrue(terminals[0]["release"]["verified"])
            self.assertFalse(backend.lease.cancel.is_set())
            names = [row.get("event") for row in events]
            self.assertLess(names.index("input_admission"),
                            names.index("input_release_measurement"))
            self.assertLess(names.index("input_release_measurement"),
                            names.index("terminal"))
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
            executor_v3.Lease = prior_lease_type


if __name__ == "__main__":
    unittest.main(verbosity=2)
