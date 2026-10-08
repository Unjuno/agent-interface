import importlib.util
import os
import sys
import threading
import time
import unittest
from pathlib import Path

PR_ROOT = Path(os.environ["PR_ROOT"])
FIX = PR_ROOT / "research/doom/map01_v39_cancel_release_fix_a01_20261005"
sys.path.insert(0, str(FIX))
spec = importlib.util.spec_from_file_location("candidate_tests", FIX / "test_cancel_release.py")
candidate_tests = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = candidate_tests
spec.loader.exec_module(candidate_tests)


class MutableReleaseRecordCustody(unittest.TestCase):
    def test_partial_record_consumed_before_aggregate_update_is_not_replayed(self):
        bridge_test, _hm, harness, lease, _bridge, backend = candidate_tests.load_candidate()
        backend.lease = lease
        aggregate_entered = threading.Event()
        allow_aggregate = threading.Event()
        screen = harness.d.screen()
        harness.d.screen = lambda: screen
        root = screen.root
        original_query_pointer = root.query_pointer

        def gated_query_pointer():
            aggregate_entered.set()
            if not allow_aggregate.wait(2):
                raise TimeoutError("aggregate query gate timed out")
            return original_query_pointer()

        root.query_pointer = gated_query_pointer
        # The candidate's actual execute() wrapper performs the final owner
        # state barrier and drain after this program returns.
        release_result = []
        release_error = []
        record_seen = []
        emitted_after_partial = []
        testcase = self

        def schedule(self, _identifier, _step):
            self.raw("F8", True)
            # Fail only the post-release per-key sample; the later aggregate
            # keymap remains available and mutates the same appended record.
            harness.d.query_fail_on.add(harness.d.query_i + 2)

            def release_owner():
                try:
                    release_result.append(harness.owner.call("release", lease))
                except BaseException as exc:
                    release_error.append(exc)

            worker = threading.Thread(target=release_owner, daemon=True)
            worker.start()
            try:
                if not aggregate_entered.wait(1):
                    raise AssertionError("aggregate phase not reached")
                record = next(row for row in harness.owner.records if row.get("event") == "owner_release")
                record_seen.append(record)
                testcase.assertFalse(record["verified"])
                testcase.assertEqual(record["per_key_release_measurements"][0]["physical_key_measurement"]["classification"],
                                     "PHYSICAL_SAMPLE_UNAVAILABLE")
                self._drain_owner_records()
                emitted_after_partial.append(len(backend.events))
                allow_aggregate.set()
                worker.join(1)
                testcase.assertFalse(worker.is_alive(), "owner release did not finish")
                testcase.assertEqual(release_error, [])
                testcase.assertTrue(release_result[0]["verified"])
                lease.cancel.set()
            finally:
                allow_aggregate.set()
                worker.join(1)
        try:
            candidate_tests.run_program(bridge_test, backend, lease, schedule,
                                        identifier="record-custody-a02", step=3)
            record = record_seen[0]
            self.assertTrue(record["verified"])
            self.assertEqual(record["keys_down"], [])
            # execute()'s finally block has now performed the final drain.
            self.assertEqual(len(backend.events), emitted_after_partial[0])
            receipts = [row for row in backend.events if row.get("event") == "input_release_measurement"]
            self.assertEqual(len(receipts), 1)
            self.assertEqual(receipts[0]["physical_key_measurement"]["classification"],
                             "PHYSICAL_SAMPLE_UNAVAILABLE")
            self.assertNotEqual(receipts[0]["physical_key_measurement"]["classification"],
                                "CONFIRMED_PHYSICAL_UP")
            self.assertEqual(harness.d.physical, set())
        finally:
            harness.close()

    def test_focus_invalid_exit_drains_partial_before_release_barrier(self):
        bridge_test, _hm, harness, _lease, _bridge, backend = candidate_tests.load_candidate()
        import executor_v3

        prior_lease = executor_v3.Lease

        class ObservedLease(prior_lease):
            def __init__(self, deadline):
                super().__init__(deadline)
                self.expected_focus = 42
                self.intent_token = "intent-focus-invalid-custody-a02"

        executor_v3.Lease = ObservedLease
        parent = bridge_test.Backend.__bases__[0]
        missing = object()
        prior_execute = parent.__dict__.get("execute", missing)
        prior_release = parent.__dict__.get("release_all", missing)
        events = []
        aggregate_entered = threading.Event()
        allow_aggregate = threading.Event()
        partial_drained = threading.Event()
        terminal_seen = threading.Event()
        admission_seen = threading.Event()
        release_errors = []
        release_thread = []
        screen = harness.d.screen()
        harness.d.screen = lambda: screen
        root = screen.root
        original_query_pointer = root.query_pointer

        def gated_query_pointer():
            aggregate_entered.set()
            if not allow_aggregate.wait(2):
                raise TimeoutError("aggregate query gate timed out")
            return original_query_pointer()

        root.query_pointer = gated_query_pointer
        original_drain = backend._drain_owner_records

        def observed_drain():
            result = original_drain()
            rows = [row for row in harness.owner.records if row.get("event") == "owner_release"]
            if aggregate_entered.is_set() and rows and not rows[0].get("verified", False):
                partial_drained.set()
                allow_aggregate.set()
            return result

        backend._drain_owner_records = observed_drain

        def emit(row):
            events.append(row)
            if row.get("event") == "input_admission":
                admission_seen.set()
            if row.get("event") == "terminal":
                terminal_seen.set()

        testcase = self

        def focus_invalid_program(self, _step, _cancel, _identifier, _index):
            self.raw("F8", True)
            harness.d.query_fail_on.add(harness.d.query_i + 2)

            def release_owner():
                try:
                    harness.owner.call("release", self.lease)
                except BaseException as exc:
                    release_errors.append(exc)

            worker = threading.Thread(target=release_owner, daemon=True)
            release_thread.append(worker)
            worker.start()
            if not aggregate_entered.wait(1):
                raise AssertionError("aggregate phase not reached")
            raise executor_v3.DecisionRequired()

        def release_all(self):
            try:
                release = self.owner.call("release", self.lease)
            finally:
                self._drain_owner_records()
            state = self.owner.call("input_state", self.lease)
            return {"verified": (release.get("verified") is True
                                 and state.get("owned_keycodes") == []
                                 and state.get("owned_buttons") == [])}

        parent.execute = focus_invalid_program
        parent.release_all = release_all
        backend.sequence = 1
        backend.validate = lambda _steps: None
        backend.emit = emit
        executor = executor_v3.Executor(backend, emit)
        try:
            executor.submit("focus-invalid-custody-a02", [{"op": "hold"}], 1,
                            time.perf_counter_ns() + 10_000_000_000)
            testcase.assertTrue(admission_seen.wait(1), repr(events))
            testcase.assertTrue(terminal_seen.wait(1), repr(events))
            for worker in release_thread:
                worker.join(1)
                testcase.assertFalse(worker.is_alive(), "initial owner release remained blocked")
            testcase.assertTrue(partial_drained.is_set(), "execute-exit did not drain the partial record")
            testcase.assertEqual(release_errors, [])
            record = next(row for row in harness.owner.records if row.get("event") == "owner_release")
            testcase.assertTrue(record["verified"])
            testcase.assertEqual(record["keys_down"], [])
            ups = [row for row in events if row.get("event") == "input_release_measurement"]
            downs = [row for row in events if row.get("event") == "input_admission"]
            terminals = [row for row in events if row.get("event") == "terminal"]
            testcase.assertEqual(len(ups), 1, repr(events))
            testcase.assertEqual(ups[0]["physical_key_measurement"]["classification"],
                                 "PHYSICAL_SAMPLE_UNAVAILABLE")
            testcase.assertEqual(ups[0]["physical_key_measurement"]["actuation_id"],
                                 downs[0]["physical_key_measurement"]["actuation_id"])
            testcase.assertEqual(len(terminals), 1)
            testcase.assertEqual(terminals[0]["status"], "needs_decision", repr(events))
            testcase.assertTrue(terminals[0]["release"]["verified"])
            testcase.assertEqual(harness.d.physical, set())
        finally:
            allow_aggregate.set()
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
            executor_v3.Lease = prior_lease


if __name__ == "__main__":
    unittest.main(verbosity=2)
