import unittest

from audit import _strict_overlap, validate_complete_row


class IntervalAuditTests(unittest.TestCase):
    def test_strict_overlap_and_non_overlap(self):
        self.assertTrue(_strict_overlap(10, 20, 15, 25))
        self.assertFalse(_strict_overlap(10, 20, 20, 30))
        self.assertFalse(_strict_overlap(10, 20, 1, 9))

    def test_valid_row_and_frozen_mutations(self):
        expected = {3789: {"sha256": "a" * 64, "bytes": 12}}
        row = {
            "pid": 123,
            "phase_before": 0,
            "open_start_ns": 10,
            "open_end_ns": 12,
            "read_start_ns": 12,
            "read_end_ns": 14,
            "bytes": 12,
            "raw_sha256": "a" * 64,
            "parse_ok": True,
            "generation": 3789,
            "package_valid": True,
        }
        self.assertTrue(validate_complete_row(row, expected, 123))
        mutations = (
            {"pid": 999},
            {"parse_ok": False},
            {"package_valid": False},
            {"generation": 9999},
            {"raw_sha256": "0" * 64},
            {"bytes": 13},
            {"open_end_ns": 10},
            {"phase_before": 99},
        )
        for mutation in mutations:
            with self.subTest(mutation=mutation):
                changed = dict(row)
                changed.update(mutation)
                self.assertFalse(validate_complete_row(changed, expected, 123))


if __name__ == "__main__":
    unittest.main()
