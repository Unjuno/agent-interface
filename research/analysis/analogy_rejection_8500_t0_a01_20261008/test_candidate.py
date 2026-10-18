import unittest

from candidate import score_candidate


class StructuredMemoryBoundaryTests(unittest.TestCase):
    def test_changed_target_envelope_reopens_valid_candidate(self):
        candidate = {
            "candidate_id": "R01",
            "counterexample_id": "CE01",
            "lexical_similarity": 0.91,
            "relation_valid": True,
            "boundary_matches": False,
        }
        target = {"target_id": "T01-V2", "envelope_version": 2}
        memory = [{"counterexample_id": "CE01", "boundary_field": "objective"}]

        result = score_candidate(candidate, target, "structured", memory)

        self.assertEqual("PROPOSE", result["decision"])
        self.assertEqual("BOUNDARY_NO_LONGER_APPLIES_FRESH_CHECK_PASSED", result["reason"])
        self.assertFalse(result["automatic_exclusion"])

    def test_applicable_counterexample_prompts_fresh_check_and_rejects(self):
        candidate = {
            "candidate_id": "R01",
            "counterexample_id": "CE01",
            "lexical_similarity": 0.91,
            "relation_valid": False,
            "boundary_matches": True,
        }
        target = {"target_id": "T01-V1", "envelope_version": 1}
        memory = [{"counterexample_id": "CE01", "boundary_field": "objective"}]

        result = score_candidate(candidate, target, "structured", memory)

        self.assertEqual("REJECT", result["decision"])
        self.assertEqual("APPLICABLE_COUNTEREXAMPLE_FRESH_CHECK_FAILED", result["reason"])
        self.assertTrue(result["fresh_check_performed"])
        self.assertFalse(result["automatic_exclusion"])

    def test_missing_fresh_relation_evidence_is_unknown_not_rejected(self):
        candidate = {
            "candidate_id": "R01",
            "counterexample_id": "CE01",
            "lexical_similarity": 0.91,
            "relation_valid": None,
            "boundary_matches": True,
        }
        target = {"target_id": "T01-V1", "envelope_version": 1}
        memory = [{"counterexample_id": "CE01", "boundary_field": "objective"}]

        result = score_candidate(candidate, target, "structured", memory)

        self.assertEqual("UNKNOWN", result["decision"])
        self.assertEqual("FRESH_CHECK_EVIDENCE_MISSING", result["reason"])


if __name__ == "__main__":
    unittest.main()
