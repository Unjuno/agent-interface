"""Fail-closed projection tests for legacy V39 owner identity joins."""
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import map01_overlap_controller_v39 as controller


def legacy_pair():
    return [
        {
            "event": "input_admission", "id": "program-1", "step": 0,
            "key": "F8", "intent_token": "intent-1", "owner_id": "owner-1",
            "admitted_ns": 10, "input_ack_ns": 20,
        },
        {
            "event": "input_release_transition", "id": "program-1", "step": 0,
            "key": "F8", "intent_token": "intent-1", "owner_id": "owner-1",
            "operation": "up", "release_call_started_ns": 30,
            "release_call_returned_ns": 60,
            "owner_thread_keyup_history_complete": True,
            "owner_thread_keyup_verified": True,
            "owner_thread_keyup_receipt": {
                "event": "owner_explicit_keyup", "key": "F8",
                "intent_token": "intent-1", "owner_id": "owner-1",
                "server_sync_completed": True,
                "owner_keyrelease_started_ns": 40,
                "owner_sync_returned_ns": 50,
            },
        },
    ]


class V39LegacyOwnerIdentityTests(unittest.TestCase):
    def test_partial_null_or_conflicting_owner_ids_do_not_pair_timing(self):
        cases = (
            ("admission_missing", 0, ("owner_id",), "missing"),
            ("admission_null", 0, ("owner_id",), "null"),
            ("admission_conflict", 0, ("owner_id",), "conflict"),
            ("transition_missing", 1, ("owner_id",), "missing"),
            ("transition_null", 1, ("owner_id",), "null"),
            ("transition_conflict", 1, ("owner_id",), "conflict"),
            ("nested_missing", 1, ("owner_thread_keyup_receipt", "owner_id"), "missing"),
            ("nested_null", 1, ("owner_thread_keyup_receipt", "owner_id"), "null"),
            ("nested_conflict", 1, ("owner_thread_keyup_receipt", "owner_id"), "conflict"),
        )
        for label, index, path, mutation in cases:
            with self.subTest(case=label):
                events = legacy_pair()
                row = events[index]
                for field in path[:-1]:
                    row = row[field]
                field = path[-1]
                if mutation == "missing":
                    row.pop(field)
                elif mutation == "null":
                    row[field] = None
                else:
                    row[field] = "owner-2"

                receipt = controller.input_edge_receipts(events)[0]

                self.assertEqual(receipt["status"], "release_receipt_incomplete")
                self.assertIsNone(receipt["admitted_to_owner_keyup_start_ms"])
                self.assertIsNone(receipt["input_ack_to_owner_keyup_start_ms"])

    def test_all_owner_ids_absent_legacy_pair_remains_supported(self):
        events = legacy_pair()
        events[0].pop("owner_id")
        events[1].pop("owner_id")
        events[1]["owner_thread_keyup_receipt"].pop("owner_id")

        receipt = controller.input_edge_receipts(events)[0]

        self.assertEqual(receipt["status"], "paired")
        self.assertEqual(receipt["admitted_to_owner_keyup_start_ms"], 0.00003)

    def test_matching_explicit_owner_ids_remain_supported(self):
        receipt = controller.input_edge_receipts(legacy_pair())[0]

        self.assertEqual(receipt["status"], "paired")
        self.assertEqual(receipt["admitted_to_owner_keyup_start_ms"], 0.00003)


if __name__ == "__main__":
    unittest.main(verbosity=2)
