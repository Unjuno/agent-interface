import sys
from pathlib import Path
import time
import unittest

sys.path.insert(0, str(Path(__file__).parent))

from input_owner_process_v1 import (  # noqa: E402
    decode_lease,
    encode_lease,
    read_recovery_receipt,
    _receipt_is_verified,
    validate_request,
)
from lease_release_v1 import Lease  # noqa: E402


class InputOwnerProcessProtocolTests(unittest.TestCase):
    def make_lease(self):
        lease = Lease(time.perf_counter_ns() + 5_000_000_000)
        lease.expected_focus = 42
        lease.expected_surface = 84
        lease.expected_geometry = [0, 0, 320, 240]
        return lease

    def test_lease_wire_preserves_identity_deadline_focus_and_surface(self):
        lease = self.make_lease()
        lease.intent_token = "intent-1"
        wire = encode_lease(lease)
        self.assertEqual(wire["deadline_ns"], lease.deadline)
        self.assertEqual(wire["intent_token"], "intent-1")
        self.assertEqual(wire["expected_focus"], 42)
        self.assertEqual(wire["expected_surface"], 84)
        self.assertEqual(wire["expected_geometry"], [0, 0, 320, 240])
        restored = decode_lease(wire, {})
        self.assertEqual(restored.deadline, lease.deadline)
        self.assertEqual(restored.intent_token, "intent-1")
        self.assertEqual(restored.expected_focus, 42)
        self.assertEqual(restored.expected_surface, 84)
        self.assertEqual(restored.expected_geometry, [0, 0, 320, 240])

    def test_repeated_token_returns_same_server_lease_and_propagates_cancel(self):
        lease = self.make_lease()
        lease.intent_token = "intent-2"
        leases = {}
        first = decode_lease(encode_lease(lease), leases)
        lease.cancel.set()
        second = decode_lease(encode_lease(lease), leases)
        self.assertIs(first, second)
        self.assertTrue(second.cancel.is_set())

    def test_request_requires_exact_wire_fields_and_monotonic_id(self):
        lease = self.make_lease()
        lease.intent_token = "intent-3"
        request = {
            "schema": "input-owner-rpc-v1",
            "request_id": 1,
            "op": "down",
            "lease": encode_lease(lease),
            "key": "a",
        }
        self.assertEqual(validate_request(request, expected_id=1)["op"], "down")
        with self.assertRaisesRegex(ValueError, "exact request fields"):
            validate_request({**request, "shell": "xterm"}, expected_id=1)

    def test_replayed_request_id_and_unallowlisted_key_are_rejected(self):
        lease = self.make_lease()
        lease.intent_token = "intent-4"
        request = {"schema": "input-owner-rpc-v1", "request_id": 3,
                   "op": "down", "lease": encode_lease(lease), "key": "a"}
        with self.assertRaisesRegex(ValueError, "request id"):
            validate_request(request, expected_id=2)
        with self.assertRaisesRegex(ValueError, "key not allowlisted"):
            validate_request({**request, "key": "xterm"}, expected_id=3)

    def test_keyboard_admission_requires_observed_focus_binding(self):
        lease = self.make_lease()
        lease.intent_token = "intent-5"
        wire = encode_lease(lease)
        wire["expected_focus"] = None
        request = {"schema": "input-owner-rpc-v1", "request_id": 1,
                   "op": "down", "lease": wire, "key": "a"}
        with self.assertRaisesRegex(ValueError, "observed focus"):
            validate_request(request, expected_id=1)

    def test_up_batch_rejects_unhashable_or_duplicate_key_items(self):
        lease = self.make_lease()
        lease.intent_token = "intent-batch"
        request = {"schema": "input-owner-rpc-v1", "request_id": 1,
                   "op": "up_batch", "lease": encode_lease(lease),
                   "key": [["a"]]}
        with self.assertRaisesRegex(ValueError, "unique allowlisted"):
            validate_request(request, expected_id=1)
        request["key"] = ["a", "a"]
        with self.assertRaisesRegex(ValueError, "unique allowlisted"):
            validate_request(request, expected_id=1)

    def test_recovery_receipt_requires_one_verified_release_record(self):
        release = {"event": "owner_release", "verified": True,
                   "keys_down": [], "buttons_down": [], "keys_unknown": [],
                   "key_state_errors": []}
        receipt = {"schema": "input-owner-recovery-v1", "receipt_fsynced": True,
                   "owner_thread_stopped": True, "close_error": None,
                   "release_records": [release]}
        self.assertTrue(_receipt_is_verified(receipt))
        receipt["release_records"] = [release, release]
        self.assertFalse(_receipt_is_verified(receipt))


if __name__ == "__main__":
    unittest.main()
