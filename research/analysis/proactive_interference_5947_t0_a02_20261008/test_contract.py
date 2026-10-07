"""A02 T0 contract tests; candidate and auditor are intentionally not present yet.

Run only during construction, before freeze. Never run after a formal CLI invocation.
"""
import unittest

from candidate import build_corpus
from auditor import audit_corpus


class ContractTests(unittest.TestCase):
    def test_corpus_cardinality_and_strata(self):
        rows = build_corpus()
        self.assertEqual(len(rows), 50)
        self.assertEqual(sum(r["kind"] == "matched" for r in rows), 48)
        self.assertEqual(sum(r["kind"] == "position_control" for r in rows), 2)
        self.assertEqual(len({(r["condition"], r["depth"], r["arm"]) for r in rows if r["kind"] == "matched"}), 48)

    def test_complete_identity_and_serialized_slot(self):
        rows = build_corpus()
        groups = {}
        for row in rows:
            if row["kind"] == "matched":
                groups.setdefault((row["condition"], row["depth"]), []).append(row)
        for group in groups.values():
            self.assertEqual(len({r["baseline"] for r in group}), 1)
            self.assertEqual(len({r["baseline_source_id"] for r in group}), 1)
            self.assertEqual(len({r["task_bytes"] for r in group}), 1)
            self.assertEqual(len({r["query_bytes"] for r in group}), 1)
            self.assertEqual(len({r["prefix_bytes"] for r in group}), 1)
            self.assertEqual(len({r["suffix_bytes"] for r in group}), 1)
            self.assertEqual(len({r["current_cue_offset"] for r in group}), 1)
            for row in group:
                context = row["prefix_bytes"] + row["history_slot_bytes"] + row["suffix_bytes"]
                self.assertEqual(context, row["serialized_context_bytes"])
                self.assertEqual(row["history_slot_start"], len(row["prefix_bytes"]))
                self.assertEqual(row["history_slot_end"], len(row["prefix_bytes"]) + len(row["history_slot_bytes"]))
            self.assertEqual(len({len(r["serialized_context_bytes"]) for r in group}), 1)

    def test_unknown_is_explicit_and_not_answered(self):
        rows = [r for r in build_corpus() if r["condition"] == "unsupported"]
        self.assertEqual(len(rows), 16)
        self.assertTrue(all(r["outcome"] == "UNKNOWN_UNSUPPORTED" and r["answer"] is None and r["reason"] for r in rows))

    def test_position_pair_changes_only_cue_offset(self):
        rows = [r for r in build_corpus() if r["kind"] == "position_control"]
        self.assertEqual(len(rows), 2)
        a, b = rows
        for key in a:
            if key != "current_cue_offset":
                self.assertEqual(a[key], b[key], key)
        self.assertNotEqual(a["current_cue_offset"], b["current_cue_offset"])

    def test_independent_auditor_accepts_frozen_corpus(self):
        result = audit_corpus(build_corpus())
        self.assertEqual(result["result"], "PASS")
        self.assertEqual(result["matched_rows"], 48)
        self.assertEqual(result["position_rows"], 2)
        self.assertEqual(result["errors"], [])

    def test_eight_corruptions_rejected(self):
        rows = build_corpus()
        mutations = (
            "final_truth", "baseline_identity", "common_byte", "cue_offset",
            "lineage", "observed_inference", "unknown_answer", "unsupported_omitted",
        )
        for mutation in mutations:
            with self.subTest(mutation=mutation):
                altered = apply_mutation(rows, mutation)
                self.assertNotEqual(audit_corpus(altered)["result"], "PASS", mutation)


if __name__ == "__main__":
    unittest.main()
