"""Construction test for cancellation-cause plus owner key-up receipt composition."""
from __future__ import annotations

import sys
import time
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(1, str(HERE.parents[1] / "FROZEN" / "current-main" / "research" / "live_control"))

from lease_release_v1 import Lease
from test_executor_owner_cancel_cause_v1 import make_owner


class ComposedCancelKeyupBoundaryTests(unittest.TestCase):
    def test_explicit_keyup_receipt_and_post_io_cancel_cause_coexist(self):
        previous_transition_module = sys.modules.pop("input_transition_owner_v4", None)
        previous_candidate_owner = sys.modules.pop("input_owner_v12", None)
        wrapped, displays, _constants, _dequeued, _lease_slot, _owner_thread, saved = make_owner()
        self.assertTrue(wrapped._inner.ready.wait(1))
        # The helper's instance-level queue hook is specific to its executor race test.
        del wrapped._inner.requests.get
        lease = Lease(time.perf_counter_ns() + 5_000_000_000)
        lease.expected_focus = 41
        lease.focus_invalid = False
        try:
            wrapped.call("down", lease, "a")
            keyup = wrapped.call("up", lease, "a")
            self.assertEqual(keyup["event"], "input_release_transition")
            self.assertTrue(keyup["owner_thread_keyup_verified"])
            self.assertFalse(keyup["owner_thread_keyup_receipt"]["physical_verification_authoritative"])
            self.assertEqual(keyup["owner_thread_keyup_receipt"]["operation"], "up")

            original_sync = displays[0].sync
            armed = [True]

            def cancel_during_release_sync():
                original_sync()
                if armed[0]:
                    armed[0] = False
                    lease.set()

            displays[0].sync = cancel_during_release_sync
            released = wrapped.call("release", lease)
            self.assertEqual(released["event"], "owner_release")
            self.assertEqual(released["reason"], "cancelled")
            self.assertTrue(released["verified"])
            self.assertEqual(released["keys_down"], [])
            self.assertEqual(lease.interruption_snapshot()["record"]["reason"], "cancelled")

            history = wrapped.records
            self.assertEqual(sum(row.get("event") == "owner_explicit_keyup" for row in history), 1)
            self.assertEqual(sum(row.get("event") == "owner_release" for row in history), 1)
        finally:
            wrapped.close()
            sys.modules.pop("input_transition_owner_v4", None)
            if previous_transition_module is not None:
                sys.modules["input_transition_owner_v4"] = previous_transition_module
            if previous_candidate_owner is not None:
                sys.modules["input_owner_v12"] = previous_candidate_owner
            for name, module in saved.items():
                if module is None:
                    sys.modules.pop(name, None)
                else:
                    sys.modules[name] = module


if __name__ == "__main__":
    unittest.main(verbosity=2)
