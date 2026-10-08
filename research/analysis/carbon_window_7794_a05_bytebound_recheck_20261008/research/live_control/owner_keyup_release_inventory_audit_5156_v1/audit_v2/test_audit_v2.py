import copy
import json
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
STUDY = HERE.parent
sys.path.insert(0, str(STUDY))

from audit_request_sequences import audit_owner_behavior


class AuditV2Tests(unittest.TestCase):
    def test_accepts_the_frozen_recorded_request_sequence(self):
        run = json.loads((STUDY / "RUN_BYTE_IDENTICAL.json").read_text())
        self.assertEqual(audit_owner_behavior(run["owner_behavior"]), [])

    def test_rejects_contradictory_request_arrays_when_flag_stays_true(self):
        behavior = self.recorded_owner_behavior()
        behavior["v11_requests"][0] = [99, 999]
        self.assertIn("request_sequence_mismatch", audit_owner_behavior(behavior))

    def test_rejects_identically_wrong_arrays(self):
        behavior = self.recorded_owner_behavior()
        behavior["v10_requests"][0] = [99, 999]
        behavior["v11_requests"][0] = [99, 999]
        self.assertIn("request_sequence_mismatch", audit_owner_behavior(behavior))

    def test_rejects_tampered_self_reported_expected_sequence(self):
        behavior = self.recorded_owner_behavior()
        behavior["expected_request_sequence"][0] = [99, 999]
        self.assertIn("expected_sequence_mismatch", audit_owner_behavior(behavior))

    def test_rejects_boolean_event_code_as_noncanonical_integer(self):
        behavior = self.recorded_owner_behavior()
        behavior["v11_requests"][0][0] = True
        self.assertIn("request_sequence_type_invalid", audit_owner_behavior(behavior))

    def test_rejects_summary_flag_that_disagrees_with_exact_arrays(self):
        behavior = self.recorded_owner_behavior()
        behavior["v10_v11_behavior_equivalent"] = False
        self.assertIn("equivalence_flag_mismatch", audit_owner_behavior(behavior))

    @staticmethod
    def recorded_owner_behavior():
        run = json.loads((STUDY / "RUN_BYTE_IDENTICAL.json").read_text())
        return copy.deepcopy(run["owner_behavior"])


if __name__ == "__main__":
    unittest.main()
