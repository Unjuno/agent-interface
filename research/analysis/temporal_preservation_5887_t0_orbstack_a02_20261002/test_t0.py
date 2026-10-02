from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

import auditor
import candidate

ROOT = Path(__file__).parent
FIXTURE = json.loads((ROOT / "fixture.json").read_text())


class TemporalPreservationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = candidate.build(FIXTURE)

    def test_independent_audit_accepts_all_frozen_rows(self):
        result = auditor.audit(FIXTURE, self.raw)
        self.assertEqual(result, {"status": "PASS_METHOD_SCOPED", "rows_checked": 20, "errors": []})

    def test_timed_exact_stutter_is_preserved(self):
        row = next(r for r in self.raw["rows"] if r["trace_id"] == "benign_exact_timed_stutter" and r["arm"] == "exact_timed_stutter")
        self.assertTrue(all(v["status"] == "PRESERVED" for v in row["predicates"].values()))
        self.assertEqual(row["source_indices"], [0, 2])

    def test_edge_count_and_deadline_witness_losses_are_exposed(self):
        edge = next(r for r in self.raw["rows"] if r["trace_id"] == "repeated_edge_occurrence" and r["arm"] == "semantic_only")
        deadline = next(r for r in self.raw["rows"] if r["trace_id"] == "only_within_deadline_witness" and r["arm"] == "semantic_only")
        self.assertEqual(edge["predicates"]["warning_count"]["status"], "NOT_PRESERVED")
        self.assertEqual(deadline["predicates"]["commit_ack_by_deadline"]["status"], "NOT_PRESERVED")

    def test_missing_timestamp_never_certifies_deadline(self):
        row = next(r for r in self.raw["rows"] if r["trace_id"] == "missing_timestamp" and r["arm"] == "identity")
        self.assertEqual(row["predicates"]["commit_ack_by_deadline"]["status"], "UNKNOWN")

    def test_generation_transition_not_hidden_by_pixel_equal_projection(self):
        row = next(r for r in self.raw["rows"] if r["trace_id"] == "pixel_equal_generation_change" and r["arm"] == "latest_only")
        self.assertEqual(row["predicates"]["authority_changes"]["status"], "NOT_PRESERVED")

    def test_mutations_are_rejected(self):
        mutations = []
        dropped = copy.deepcopy(self.raw)
        dropped["rows"].pop()
        mutations.append(dropped)
        changed_edge = copy.deepcopy(self.raw)
        changed_edge["input"]["traces"][1]["rows"][1]["edges"] = []
        mutations.append(changed_edge)
        forged_time = copy.deepcopy(self.raw)
        forged_time["rows"][0]["predicates"]["commit_ack_by_deadline"]["full"] = False
        mutations.append(forged_time)
        for raw in mutations:
            with self.subTest(raw=raw is dropped):
                self.assertNotEqual(auditor.audit(FIXTURE, raw)["status"], "PASS_METHOD_SCOPED")


if __name__ == "__main__":
    unittest.main()
