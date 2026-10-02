"""Construction and tamper controls; never writes the formal result."""
import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import audit_successor


class AuditSuccessorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.freeze, cls.contents, cls.candidate = audit_successor.load_inputs()

    def test_unchanged_candidate_and_raw_pass_scoped_audit(self):
        result = audit_successor.audit(self.freeze, self.contents, self.candidate)
        self.assertEqual(result["status"], "PASS_AUDIT_SUCCESSOR_SCOPED", result["errors"])

    def test_predecessor_v38_zero_score_expectation_is_rejected(self):
        candidate = copy.deepcopy(self.candidate)
        candidate["domains"][0]["event_counts"]["post_control_score"] = 0
        result = audit_successor.audit(self.freeze, self.contents, candidate)
        self.assertIn("doom_v38 candidate/raw event counts differ", result["errors"])

    def test_candidate_raw_event_count_drift_is_rejected(self):
        candidate = copy.deepcopy(self.candidate)
        candidate["domains"][1]["event_counts"]["input_admission"] -= 1
        result = audit_successor.audit(self.freeze, self.contents, candidate)
        self.assertIn("doom_v39 candidate/raw event counts differ", result["errors"])

    def test_transition_witness_cardinality_and_index_are_checked(self):
        candidate = copy.deepcopy(self.candidate)
        candidate["domains"][2]["observer_transition_indices"] = [92]
        result = audit_successor.audit(self.freeze, self.contents, candidate)
        self.assertIn("OpenTTD observer transition summary differs", result["errors"])

    def test_transition_witness_and_full_observer_cardinalities_are_distinct(self):
        result = audit_successor.audit(self.freeze, self.contents, self.candidate)
        self.assertEqual(result["reconstructed"]["openttd"]["observer_transition_witnesses"], 1)
        self.assertEqual(result["reconstructed"]["openttd"]["observer_record_count"], 263)

    def test_raw_hash_tampering_is_rejected(self):
        contents = dict(self.contents)
        contents["doom-v38-events.jsonl"] += "\n"
        result = audit_successor.audit(self.freeze, contents, self.candidate)
        self.assertIn("raw hash mismatch: doom-v38-events.jsonl", result["errors"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
