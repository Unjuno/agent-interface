import copy
import json
import unittest
from pathlib import Path

from audit_v2 import audit
from normalize_join import JoinError, normalize_join


ROOT = Path(__file__).parent


def load(name):
    return json.loads((ROOT / name).read_text(encoding="utf-8"))


class JoinTests(unittest.TestCase):
    def setUp(self):
        self.expected = load("expected_inventory.json")
        self.owner_rows = load("owner_rows_v1.json")
        self.receipts = load("caller_receipts_v3.json")

    def test_repeated_explicit_key_and_autonomous_cleanup_join_then_v2_audit(self):
        joined = normalize_join(self.expected, self.owner_rows, self.receipts)
        self.assertEqual([row["release_id"] for row in joined],
                         ["explicit-a-01", "explicit-a-02", "cleanup-b-01"])
        self.assertTrue(all(row["schema"] == "owner-key-release-bracket-v2" for row in joined))
        self.assertEqual(joined[0]["caller_started_ns"], 100)
        self.assertEqual(joined[0]["caller_returned_ns"], 150)
        self.assertEqual(joined[2]["trigger_class"], "owner_lease_cleanup")
        self.assertNotIn("caller_started_ns", joined[2])
        self.assertEqual(audit(self.expected, joined), [])

    def test_direct_v1_rows_fail_v2_contract_even_if_caller_edges_are_added(self):
        direct = audit(self.expected, self.owner_rows)
        self.assertTrue(any(error.endswith(":schema") for error in direct))
        self.assertTrue(any(":missing:release_id" in error for error in direct))
        self.assertTrue(any(error.startswith("expected_release_missing:") for error in direct))
        enriched = [dict(row, caller_started_ns=100, caller_returned_ns=150)
                    for row in self.owner_rows]
        still_fails = audit(self.expected, enriched)
        self.assertTrue(any(error.endswith(":schema") for error in still_fails))
        self.assertTrue(any(":missing:release_id" in error for error in still_fails))

    def test_empty_and_all_omitted_owner_rows_fail_closed(self):
        with self.assertRaisesRegex(JoinError, "owner_release_count_mismatch"):
            normalize_join(self.expected, [], self.receipts)
        with self.assertRaisesRegex(JoinError, "owner_release_count_mismatch"):
            normalize_join(self.expected, [], [])

    def test_one_omitted_owner_row_fails(self):
        with self.assertRaisesRegex(JoinError, "owner_release_count_mismatch"):
            normalize_join(self.expected, self.owner_rows[:-1], self.receipts)

    def test_duplicate_raw_row_cannot_reuse_caller_receipt_or_expected_id(self):
        rows = self.owner_rows + [copy.deepcopy(self.owner_rows[0])]
        with self.assertRaises(JoinError):
            normalize_join(self.expected, rows, self.receipts)

    def test_wrong_identity_fails(self):
        rows = copy.deepcopy(self.owner_rows)
        rows[0]["keycode"] = 39
        with self.assertRaises(JoinError):
            normalize_join(self.expected, rows, self.receipts)

    def test_missing_explicit_caller_receipt_fails(self):
        with self.assertRaisesRegex(JoinError, "caller_receipt_count_mismatch"):
            normalize_join(self.expected, self.owner_rows, self.receipts[:1])

    def test_duplicate_explicit_caller_receipt_fails(self):
        receipts = self.receipts + [copy.deepcopy(self.receipts[0])]
        with self.assertRaisesRegex(JoinError, "caller_receipt_count_mismatch"):
            normalize_join(self.expected, self.owner_rows, receipts)

    def test_inverted_caller_interval_fails(self):
        receipts = copy.deepcopy(self.receipts)
        receipts[0]["release_call_started_ns"] = 160
        receipts[0]["release_call_returned_ns"] = 90
        with self.assertRaisesRegex(JoinError, "caller_interval_invalid"):
            normalize_join(self.expected, self.owner_rows, receipts)

    def test_owner_interval_inversion_fails(self):
        rows = copy.deepcopy(self.owner_rows)
        rows[0]["request_returned_ns"] = 110
        with self.assertRaisesRegex(JoinError, "owner_interval_invalid"):
            normalize_join(self.expected, rows, self.receipts)

    def test_overlapping_receipts_make_pairing_ambiguous(self):
        receipts = copy.deepcopy(self.receipts)
        receipts[1]["release_call_started_ns"] = 90
        receipts[1]["release_call_returned_ns"] = 160
        with self.assertRaisesRegex(JoinError, "caller_pairing_ambiguous"):
            normalize_join(self.expected, self.owner_rows, receipts)

    def test_duplicate_expected_sequence_fails(self):
        expected = copy.deepcopy(self.expected)
        expected[1]["sequence"] = 1
        with self.assertRaisesRegex(JoinError, "expected_sequence_invalid"):
            normalize_join(expected, self.owner_rows, self.receipts)

    def test_authority_or_physical_claim_fails(self):
        rows = copy.deepcopy(self.owner_rows)
        rows[0]["grants_input_authority"] = True
        with self.assertRaisesRegex(JoinError, "unsafe_claim"):
            normalize_join(self.expected, rows, self.receipts)
        rows[0]["grants_input_authority"] = False
        rows[0]["physical_key_up_claimed"] = True
        with self.assertRaisesRegex(JoinError, "unsafe_claim"):
            normalize_join(self.expected, rows, self.receipts)

    def test_unexpected_owner_release_row_fails(self):
        rows = copy.deepcopy(self.owner_rows)
        rows.append(dict(rows[-1], reason="unregistered_reason"))
        with self.assertRaises(JoinError):
            normalize_join(self.expected, rows, self.receipts)


if __name__ == "__main__":
    unittest.main(verbosity=2)
