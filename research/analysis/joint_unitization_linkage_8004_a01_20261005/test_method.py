import unittest

from audit import audit
from candidate import evaluate


FIXTURE = {
    "truth": {"opportunity_id": "fault-17", "same_underlying_opportunity": True,
              "channel_a_raw_span": [0, 4], "channel_b_raw_span": [1, 2],
              "channel_b_identity": "fault-17"},
    "segmentations": {"S0_boundary_left": {"channel_a_unit_span": [2, 4]},
                      "S1_boundary_right": {"channel_a_unit_span": [0, 2]}},
    "linkages": {"L0_false_candidate": {"channel_a_link_key": "candidate-9"},
                 "L1_oracle_candidate": {"channel_a_link_key": "fault-17"}},
    "clean_control": {"channel_a_span": [0, 4], "channel_b_span": [1, 2],
                      "channel_a_link_key": "control-1", "channel_b_link_key": "control-1"},
    "missing_channel_control": {"opportunity_id": "fault-18", "truth_present": True, "detected_by": []},
}


class JointMethodTests(unittest.TestCase):
    def test_joint_only_interaction_is_identified_and_audited(self):
        result = evaluate(FIXTURE)
        self.assertEqual(result["factorial"]["baseline_linked"], False)
        self.assertEqual(result["factorial"]["segmentation_only_linked"], False)
        self.assertEqual(result["factorial"]["linkage_only_linked"], False)
        self.assertEqual(result["factorial"]["joint_linked"], True)
        self.assertTrue(result["factorial"]["one_factor_ranges_stable"])
        self.assertTrue(result["factorial"]["joint_changes_decision"])
        self.assertTrue(audit(FIXTURE, result)["ok"])

    def test_mutated_joint_cell_is_rejected(self):
        result = evaluate(FIXTURE)
        result["rows"][-1]["linked"] = False
        report = audit(FIXTURE, result)
        self.assertFalse(report["ok"])
        self.assertTrue({"raw_assignment_reconstruction", "candidate_row_reconstruction", "capture_history"} & set(report["errors"]))

    def test_mutated_denominator_is_rejected(self):
        result = evaluate(FIXTURE)
        result["rows"].pop()
        self.assertIn("assignment_denominator", audit(FIXTURE, result)["errors"])


if __name__ == "__main__":
    unittest.main()
