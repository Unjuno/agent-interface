import unittest

import independent_audit_v3


class VersionedGateRepairTests(unittest.TestCase):
    def test_four_recomputed_label_mismatches_reproduce_frozen_gate(self):
        mismatches = [
            "baseline:expected_ordered_mismatch:4",
            "baseline:expected_ordered_mismatch:15",
            "candidate:expected_ordered_mismatch:4",
            "candidate:expected_ordered_mismatch:15",
        ]
        result = independent_audit_v3.decide(
            baseline_auditor_pass=True,
            mutated_auditor_pass=True,
            baseline_errors=[],
            mutated_errors=mismatches + ["status/output consistency errors"],
        )
        self.assertEqual("PASS_REPRODUCED_AUDITOR_FALSE_PASS", result["outcome"])
        self.assertEqual(4, result["chronology_label_mismatch_count"])

    def test_failed_original_auditor_or_wrong_mismatch_count_does_not_reproduce(self):
        four = [f"expected_ordered_mismatch:{i}" for i in range(4)]
        failed_auditor = independent_audit_v3.decide(True, False, [], four)
        too_few = independent_audit_v3.decide(True, True, [], four[:3])
        self.assertEqual("HOLD_NOT_REPRODUCED", failed_auditor["outcome"])
        self.assertEqual("HOLD_NOT_REPRODUCED", too_few["outcome"])


if __name__ == "__main__":
    unittest.main()
