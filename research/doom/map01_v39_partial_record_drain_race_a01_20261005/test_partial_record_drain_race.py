import sys
import threading
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
FIX = ROOT / "research" / "doom" / "map01_v39_cancel_release_fix_a01_20261005"
sys.path.insert(0, str(FIX))
import test_cancel_release as candidate
from executor_v3 import Expired


class PartialRecordDrainRace(unittest.TestCase):
    V3 = ROOT / "research" / "doom" / "map01_v39_cancel_release_fix_a01_20261005" / "bridge_v3_candidate.py"

    def run_case(self, sample_failure, repaired=False):
        config = {"query_fail_on": {4}} if sample_failure else {}
        original_bridge_path = candidate.BRIDGE_V2_PATH
        if repaired:
            candidate.BRIDGE_V2_PATH = self.V3
        try:
            bridge_test, harness_module, harness, lease, _bridge, backend = candidate.load_candidate(config)
        finally:
            candidate.BRIDGE_V2_PATH = original_bridge_path
        aggregate_started = threading.Event()
        aggregate_resume = threading.Event()
        barrier_snapshot = {}
        old_screen = harness.d.screen

        class RootProxy:
            def query_pointer(self):
                aggregate_started.set()
                if not aggregate_resume.wait(3):
                    raise TimeoutError("aggregate query block expired")
                return old_screen().root.query_pointer()

        harness.d.screen = lambda: type("Screen", (), {"root": RootProxy()})()
        original_call = harness.owner.call
        if repaired:
            def signaled_call(operation, *args, **kwargs):
                if operation == "release":
                    records_now = [row for row in harness.owner.records if row.get("event") == "owner_release"]
                    barrier_snapshot["bridge_held_before_barrier"] = set(backend.held)
                    barrier_snapshot["latest_record_verified_before_barrier"] = records_now[-1].get("verified")
                    aggregate_resume.set()
                return original_call(operation, *args, **kwargs)
            harness.owner.call = signaled_call

        def program(self, _identifier, _step):
            self.raw("F8", True)
            self.lease.deadline = time.perf_counter_ns() - 1
            if not aggregate_started.wait(3):
                raise AssertionError("owner did not reach aggregate pointer query")
            raise Expired()

        try:
            with self.assertRaises(Expired):
                candidate.run_program(bridge_test, backend, lease, program)

            records = [row for row in harness.owner.records if row.get("event") == "owner_release"]
            if repaired:
                self.assertGreaterEqual(len(records), 2)
                self.assertTrue(all(row.get("verified") is True for row in records))
            else:
                self.assertEqual(len(records), 1)
            record = records[0]
            self.assertEqual(len(record["per_key_release_measurements"]), 1)
            expected = "PHYSICAL_SAMPLE_UNAVAILABLE" if sample_failure else "CONFIRMED_PHYSICAL_UP"
            self.assertEqual(record["per_key_release_measurements"][0]["physical_key_measurement"]["classification"],
                             expected)
            if not repaired:
                self.assertFalse(record["verified"])
            held_during_block = set(backend.held)
            aggregate_resume.set()

            deadline = time.monotonic() + 3
            while time.monotonic() < deadline and record.get("verified") is not True:
                time.sleep(.002)
            self.assertTrue(record.get("verified"))
            self.assertEqual(record.get("keys_down"), [])
            self.assertEqual(harness.d.physical, set())
            if repaired:
                state = harness.owner.call("input_state", lease)
                self.assertEqual(state.get("owned_keycodes"), [])
                self.assertEqual(state.get("owned_buttons"), [])
            return held_during_block, set(backend.held), barrier_snapshot
        finally:
            aggregate_resume.set()
            harness.close()

    def test_confirmed_per_key_up_clears_bridge_hold_before_aggregate_returns(self):
        during, after, _snapshot = self.run_case(sample_failure=False)
        self.assertEqual(during, set())
        self.assertEqual(after, set())

    def test_unavailable_per_key_sample_leaves_stale_bridge_hold_after_owner_verifies_empty(self):
        during, after, _snapshot = self.run_case(sample_failure=True)
        self.assertEqual(during, {"F8"})
        self.assertEqual(after, {"F8"})

    def test_v3_completion_barrier_clears_bridge_hold_after_empty_verification(self):
        _during, after, snapshot = self.run_case(sample_failure=True, repaired=True)
        self.assertEqual(snapshot["bridge_held_before_barrier"], {"F8"})
        self.assertFalse(snapshot["latest_record_verified_before_barrier"])
        self.assertEqual(after, set())

    def test_v3_cancellation_keeps_one_contextual_release_receipt(self):
        from test_cancel_release import one_key_cancel
        original_bridge_path = candidate.BRIDGE_V2_PATH
        candidate.BRIDGE_V2_PATH = self.V3
        try:
            bridge_test, _harness_module, harness, lease, _bridge, backend = candidate.load_candidate()
        finally:
            candidate.BRIDGE_V2_PATH = original_bridge_path
        try:
            candidate.run_program(bridge_test, backend, lease, one_key_cancel)
            rows = [row for row in backend.events if row.get("event") == "input_release_measurement"]
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["physical_key_measurement"]["classification"], "CONFIRMED_PHYSICAL_UP")
            self.assertEqual(backend.held, set())
            self.assertEqual(harness.d.physical, set())
        finally:
            harness.close()


if __name__ == "__main__":
    unittest.main(verbosity=2)
