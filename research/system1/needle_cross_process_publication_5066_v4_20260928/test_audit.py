import unittest

from audit import (
    _strict_overlap,
    boundary_corruption_controls,
    validate_complete_row,
    validate_reader_exit_after_reads,
    validate_readiness_records,
    validate_reader_trace_rows,
    validate_diagnostic_complete_row,
    validate_writer_envelope,
    diagnostic_complete_generation_allowed,
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
            {"phase_before": True},
        )
        for mutation in mutations:
            with self.subTest(mutation=mutation):
                changed = dict(row)
                changed.update(mutation)
                self.assertFalse(validate_complete_row(changed, expected, 123))

    def test_diagnostic_generation_is_phase_specific(self):
        expected = {
            generation: {"sha256": str(generation), "bytes": 12}
            for generation in (3788, 7885, 4000)
        }

        def row(phase, generation):
            return {
                "pid": 123, "phase_before": phase,
                "open_start_ns": 10, "open_end_ns": 12,
                "read_start_ns": 12, "read_end_ns": 14,
                "bytes": 12, "raw_sha256": str(generation),
                "parse_ok": True, "generation": generation,
                "package_valid": True,
            }

        for phase, generation in ((0, 3788), (1, 3788), (1, 7885), (2, 7885)):
            candidate = row(phase, generation)
            self.assertTrue(diagnostic_complete_generation_allowed(candidate))
            self.assertTrue(validate_diagnostic_complete_row(candidate, expected, 123))
        for phase in (0, 1, 2):
            candidate = row(phase, 4000)
            with self.subTest(row=candidate):
                self.assertFalse(diagnostic_complete_generation_allowed(candidate))
                self.assertFalse(validate_diagnostic_complete_row(candidate, expected, 123))
        boolean_phase = row(True, 3788)
        self.assertFalse(diagnostic_complete_generation_allowed(boolean_phase))
        self.assertFalse(validate_diagnostic_complete_row(boolean_phase, expected, 123))

    def test_writer_envelope_contains_every_publication(self):
        publications = [
            {"start_ns": 20, "end_ns": 25},
            {"start_ns": 30, "end_ns": 35},
        ]
        self.assertTrue(validate_writer_envelope(10, 40, publications))
        mutations = (
            (21, 40, publications),
            (10, 34, publications),
            (True, 40, publications),
            (10, 40, [{"start_ns": 20, "end_ns": 20}]),
            (10, 40, []),
        )
        for start, end, events in mutations:
            with self.subTest(start=start, end=end, events=events):
                self.assertFalse(validate_writer_envelope(start, end, events))

    def test_reader_exit_follows_every_read_end(self):
        rows = [
            {"read_end_ns": 20},
            {"read_end_ns": 40},
        ]
        self.assertTrue(validate_reader_exit_after_reads(40, rows))
        self.assertFalse(validate_reader_exit_after_reads(39, rows))
        self.assertFalse(validate_reader_exit_after_reads(True, rows))
        self.assertFalse(validate_reader_exit_after_reads(50, [{"read_end_ns": True}]))

    def test_reader_summary_rejects_error_and_observation_cap(self):
        from audit import validate_reader_summary_execution
        good = {"limit_hit": False, "error": None, "partial_observations": 1}
        self.assertEqual(validate_reader_summary_execution(good), [])
        self.assertTrue(validate_reader_summary_execution({**good, "limit_hit": True}))
        self.assertTrue(validate_reader_summary_execution({**good, "error": "timeout"}))
        self.assertTrue(validate_reader_summary_execution({**good, "partial_observations": True}))

    def test_frozen_boundary_corruption_controls_reject(self):
        controls = boundary_corruption_controls()
        self.assertEqual(len(controls), 8)
        self.assertTrue(all(controls.values()), controls)

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
