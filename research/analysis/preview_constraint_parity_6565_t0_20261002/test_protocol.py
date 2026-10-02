from __future__ import annotations

import copy
import unittest

import auditor
import candidate


class PreviewParityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.payload = candidate.emit()
        cls.audit = auditor.audit(cls.payload)

    def test_complete_clean_matrix_passes_independent_reconstruction(self):
        self.assertEqual(self.audit["disposition"], "PASS_METHOD_SCOPED")
        self.assertEqual(self.audit["rows_expected"], 12)
        self.assertEqual(self.audit["rows_received"], 12)
        self.assertEqual(self.audit["errors"], [])

    def test_presentation_changes_order_only(self):
        for case_id in auditor.CASES:
            rows = [r for r in self.payload["rows"] if r["case_id"] == case_id]
            for key in ("source_task", "source_constraint", "candidate_effect", "candidate_digest",
                        "allowed_by_explicit_constraint", "agent_origin", "authority", "neutral_facts"):
                self.assertEqual(len({repr(r[key]) for r in rows}), 1, (case_id, key))

    def test_agent_origin_remains_disclosed_in_every_arm(self):
        self.assertTrue(all(r["agent_origin"] is True for r in self.payload["rows"]))

    def test_preference_revision_is_not_scored_as_truth(self):
        rows = [r for r in self.payload["rows"] if r["case_id"] == "UNSPECIFIED_PREFERENCE_REVISION"]
        self.assertTrue(all(r["allowed_by_explicit_constraint"] is None for r in rows))
        self.assertTrue(all(r["preference_status"] == "UNSCORABLE_PREFERENCE" for r in rows))

    def test_each_frozen_mutation_is_rejected(self):
        self.assertEqual(set(self.audit["mutations_rejected"]), {
            "recipient_swap", "format_swap", "remove_agent_provenance",
            "inject_quality_endorsement", "leak_oracle_label", "alter_candidate_digest"})
        self.assertTrue(all(self.audit["mutations_rejected"].values()))

    def test_changed_candidate_fact_is_detected(self):
        broken = copy.deepcopy(self.payload)
        row = next(r for r in broken["rows"] if r["case_id"] == "WRONG_RECIPIENT")
        row["candidate_effect"]["recipient"] = "different@example.test"
        self.assertEqual(auditor.audit(broken)["disposition"], "FAIL_METHOD")

    def test_missing_provenance_is_detected(self):
        broken = copy.deepcopy(self.payload)
        broken["rows"][0]["agent_origin"] = False
        self.assertEqual(auditor.audit(broken)["disposition"], "FAIL_METHOD")

    def test_missing_or_duplicate_rows_are_detected(self):
        missing = copy.deepcopy(self.payload)
        missing["rows"].pop()
        duplicate = copy.deepcopy(self.payload)
        duplicate["rows"].append(copy.deepcopy(duplicate["rows"][0]))
        self.assertEqual(auditor.audit(missing)["disposition"], "FAIL_METHOD")
        self.assertEqual(auditor.audit(duplicate)["disposition"], "FAIL_METHOD")


if __name__ == "__main__":
    unittest.main()
