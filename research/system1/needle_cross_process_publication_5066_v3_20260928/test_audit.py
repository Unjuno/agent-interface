import unittest

from audit import (
    _strict_overlap,
    validate_complete_row,
    validate_readiness_records,
    validate_reader_trace_rows,
    validate_writer_envelope,
    validate_reader_exit,
)


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

    def test_readiness_identity_and_publication_order(self):
        readiness = [
            {"reader_index": 0, "pid": 101, "ready_ns": 10},
            {"reader_index": 1, "pid": 202, "ready_ns": 12},
        ]
        by_index, errors = validate_readiness_records(readiness, 2, 20)
        self.assertEqual(errors, [])
        self.assertEqual(by_index[1], {"pid": 202, "ready_ns": 12})

        mutations = (
            ([readiness[0], {**readiness[1], "reader_index": 0}], 20),
            ([readiness[0], {**readiness[1], "pid": 101}], 20),
            ([readiness[0], {**readiness[1], "ready_ns": 21}], 20),
            ([readiness[0], {**readiness[1], "ready_ns": True}], 20),
        )
        for changed, first_publication_ns in mutations:
            with self.subTest(changed=changed):
                _, changed_errors = validate_readiness_records(
                    changed, 2, first_publication_ns)
                self.assertTrue(changed_errors)

    def test_writer_envelope_rejects_invalid_and_outside_brackets(self):
        publications = [{"start_ns": 12, "end_ns": 18}]
        self.assertTrue(validate_writer_envelope(10, 20, publications))
        invalid = (
            (None, 20, publications),
            (10, None, publications),
            (True, 20, publications),
            (20, 10, publications),
            (10, 20, [{"start_ns": 9, "end_ns": 18}]),
            (10, 20, [{"start_ns": 12, "end_ns": 21}]),
            (10, 20, [{"start_ns": True, "end_ns": 18}]),
            (10, 20, [{"start_ns": 12, "end_ns": 12}]),
        )
        for start, end, events in invalid:
            with self.subTest(start=start, end=end, events=events):
                self.assertFalse(validate_writer_envelope(start, end, events))

    def test_reader_exit_must_follow_every_recorded_read(self):
        rows = [
            {"read_end_ns": 25},
            {"read_end_ns": 30},
        ]
        self.assertTrue(validate_reader_exit(30, rows))
        self.assertTrue(validate_reader_exit(31, rows))
        self.assertFalse(validate_reader_exit(29, rows))
        self.assertFalse(validate_reader_exit(True, rows))
        self.assertFalse(validate_reader_exit(31, [{"read_end_ns": True}]))
        self.assertFalse(validate_reader_exit(31, []))

    def test_reader_attempts_bind_index_pid_and_follow_readiness(self):
        rows = [
            {"kind": "read", "reader_index": 0, "read_index": 0, "pid": 101,
             "open_start_ns": 20, "open_end_ns": 22},
            {"kind": "read", "reader_index": 0, "read_index": 1, "pid": 101,
             "open_start_ns": 23, "open_end_ns": 25},
        ]
        self.assertEqual(validate_reader_trace_rows(rows, 0, 101, 10), [])

        mutations = (
            {**rows[0], "kind": "mystery"},
            {**rows[0], "reader_index": 1},
            {**rows[0], "pid": 202},
            {**rows[0], "read_index": 1},
            {**rows[0], "open_start_ns": 9},
        )
        for changed in mutations:
            with self.subTest(changed=changed):
                self.assertTrue(validate_reader_trace_rows([changed], 0, 101, 10))


if __name__ == "__main__":
    unittest.main()
