import unittest

from experiment import enforce, run


class BufferOverflowTests(unittest.TestCase):
    def test_frozen_matrix_contains_baseline_and_proposed_policy(self):
        rows = list(run())
        self.assertEqual(len(rows), 6)
        cells = {(row["case_id"], row["policy"]): row for row in rows}
        self.assertEqual(cells[("exact_control", "FAIL_CLOSED")]["decision"], "PASS")
        self.assertEqual(cells[("dropped_mutation", "DROP_NEWEST")]["decision"], "PASS")
        self.assertEqual(cells[("dropped_mutation", "FAIL_CLOSED")]["decision"], "UNKNOWN_BUFFER_OVERFLOW")

    def test_exact_evidence_allows_matching_commit_without_overflow(self):
        result = enforce(
            [
                {"kind": "OBSERVE", "target": "t", "epoch": 7},
                {"kind": "AUTHORITY", "target": "t", "epoch": 7},
            ],
            {"kind": "COMMIT", "target": "t", "epoch": 7},
            capacity=2,
        )
        self.assertEqual(result["decision"], "PASS")
        self.assertFalse(result["overflow"])

    def test_overflowed_invalidation_never_allows_stale_commit(self):
        result = enforce(
            [
                {"kind": "OBSERVE", "target": "t", "epoch": 7},
                {"kind": "AUTHORITY", "target": "t", "epoch": 7},
                {"kind": "EXTERNAL_MUTATION", "target": "t", "epoch": 8},
            ],
            {"kind": "COMMIT", "target": "t", "epoch": 7},
            capacity=2,
        )
        self.assertEqual(result["decision"], "UNKNOWN_BUFFER_OVERFLOW")
        self.assertFalse(result["effect_emitted"])

    def test_overflow_is_distinct_from_a_proven_conflict(self):
        result = enforce(
            [
                {"kind": "OBSERVE", "target": "t", "epoch": 7},
                {"kind": "AUTHORITY", "target": "t", "epoch": 7},
                {"kind": "TELEMETRY", "target": "other", "epoch": 1},
            ],
            {"kind": "COMMIT", "target": "t", "epoch": 7},
            capacity=2,
        )
        self.assertEqual(result["decision"], "UNKNOWN_BUFFER_OVERFLOW")
        self.assertFalse(result["effect_emitted"])


if __name__ == "__main__":
    unittest.main()
