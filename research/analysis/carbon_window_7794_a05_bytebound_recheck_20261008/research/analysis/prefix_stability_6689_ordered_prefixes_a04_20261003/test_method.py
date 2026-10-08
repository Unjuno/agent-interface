"""Construction-only checks; these do not launch the frozen CLI allocation."""

import json
import unittest
from pathlib import Path

import auditor
import candidate


SPEC = json.loads(Path(__file__).with_name("input.json").read_text(encoding="utf-8"))


class OrderedPrefixMethodTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.records = candidate.build_records(SPEC)
        cls.header = cls.records[0]
        cls.rows = cls.records[1:]

    def test_trace_and_prefix_cardinality(self):
        self.assertEqual(self.header["trace_count"], 24)
        self.assertEqual(self.header["row_count"], 96)
        self.assertEqual(len({row["trace_id"] for row in self.rows}), 24)
        self.assertEqual(len(self.rows), 96)

    def test_each_trace_contains_every_prefix_once(self):
        for trace_id in {row["trace_id"] for row in self.rows}:
            observed = [row["prefix_length"] for row in self.rows if row["trace_id"] == trace_id]
            self.assertEqual(observed, [0, 1, 2, 3])

    def test_independent_raw_oracle_matches_candidate_construction(self):
        self.assertEqual(self.records, auditor.expected_records(SPEC))

    def test_incomplete_negative_keeps_the_pending_obligation_after_seal(self):
        row = next(
            row for row in self.rows
            if row["failed_obligations"]
            and row["pending_obligations"] == ["B"]
            and row["generation_sealed"]
        )
        self.assertEqual(row["disposition"], "UNRESOLVED")
        self.assertEqual(row["reason"], "mandatory_vector_incomplete")
        self.assertFalse(row["stable"])

    def test_complete_failure_does_not_wait_for_optional_source_or_seal(self):
        row = next(
            row for row in self.rows
            if row["failed_obligations"] == ["A", "B"]
            and not row["pending_obligations"]
            and not row["generation_sealed"]
        )
        self.assertEqual(row["disposition"], "FINAL_FAIL")
        self.assertEqual(row["unrelated_optional_sources_open"], ["optional_metrics"])

    def test_positive_waits_for_generation_seal(self):
        before = next(
            row for row in self.rows
            if row["prefix_length"] == 2
            and row["observed_results"] == {"A": "pass", "B": "pass"}
            and not row["generation_sealed"]
        )
        after = next(
            row for row in self.rows
            if row["trace_id"] == before["trace_id"] and row["prefix_length"] == 3
        )
        self.assertEqual(before["disposition"], "UNRESOLVED")
        self.assertEqual(before["reason"], "generation_frontier_open")
        self.assertEqual(after["disposition"], "FINAL_PASS")

    def test_same_terminal_results_have_distinct_intermediate_histories(self):
        rows = [
            row for row in self.rows
            if row["prefix_length"] == 1
            and row["trace_id"].startswith("case-01-")
        ]
        self.assertGreaterEqual(len({tuple(row["applied_event_ids"]) for row in rows}), 2)
        final_rows = [row for row in self.rows if row["prefix_length"] == 3 and row["trace_id"].startswith("case-01-")]
        self.assertEqual({row["disposition"] for row in final_rows}, {"FINAL_FAIL"})

    def test_disposition_counts_are_exclusive_and_metrics_separate(self):
        counts = self.header["disposition_counts"]
        self.assertEqual(set(counts), {"UNRESOLVED", "FINAL_FAIL", "FINAL_PASS"})
        self.assertEqual(sum(counts.values()), 96)
        self.assertEqual(set(self.header["prefix_metrics"]), {"stable_prefixes", "unresolved_prefixes"})

    def test_six_frozen_mutations_are_rejected(self):
        controls = auditor._mutation_controls(self.records, SPEC)
        self.assertEqual(len(controls), 6)
        self.assertTrue(all(item["rejected"] for item in controls))


if __name__ == "__main__":
    unittest.main(verbosity=2)
