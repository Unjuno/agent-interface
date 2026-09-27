import unittest

from intervals import assert_coverage, overlaps, qualifying_overlaps


class OverlapTests(unittest.TestCase):
    def test_half_open_boundary_does_not_count_as_overlap(self):
        self.assertFalse(overlaps(0, 10, 10, 20))
        self.assertTrue(overlaps(0, 11, 10, 20))

    def test_rejects_invalid_or_boolean_timestamps(self):
        with self.assertRaises(ValueError):
            overlaps(2, 1, 0, 3)
        with self.assertRaises(TypeError):
            overlaps(True, 2, 0, 3)

    def test_counts_read_calls_not_replace_pair_multiplicity(self):
        reads = [
            {"reader_id": "r1", "reader_pid": 101, "read_index": 0,
             "start_ns": 5, "end_ns": 15},
            {"reader_id": "r2", "reader_pid": 202, "read_index": 0,
             "start_ns": 20, "end_ns": 30},
        ]
        replaces = [{"start_ns": 10, "end_ns": 11, "replace_index": 0},
                    {"start_ns": 24, "end_ns": 25, "replace_index": 1}]
        self.assertEqual(qualifying_overlaps(reads, replaces), [("r1", 0), ("r2", 0)])

    def test_coverage_requires_exact_denominator_and_multiple_readers(self):
        replaces = [{"start_ns": i * 10, "end_ns": i * 10 + 1, "replace_index": i}
                    for i in range(4096)]
        reads = []
        for reader in ("r1", "r2"):
            for i in range(16):
                start = i * 10
                reads.append({"reader_id": reader, "reader_pid": 101 if reader == "r1" else 202,
                              "read_index": i,
                              "start_ns": start, "end_ns": start + 1})
        self.assertEqual(len(assert_coverage(reads, replaces)), 32)
        with self.assertRaisesRegex(ValueError, "overlaps"):
            assert_coverage(reads[:31], replaces)
        with self.assertRaisesRegex(ValueError, "4096"):
            assert_coverage(reads, replaces[:-1])


if __name__ == "__main__":
    unittest.main()
