import copy
import json
import sys
import unittest
from pathlib import Path

from audit_top_level import audit_top_level


ROOT = Path(__file__).parent
FROZEN = ROOT.parent / "protective_local_adaptation_6367_t0_20261004"
sys.path.insert(0, str(FROZEN))
from auditor import audit as audit_frozen_v1


class TopLevelReauditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = json.loads((FROZEN / "fixture.json").read_text())
        cls.events = json.loads((FROZEN / "events.json").read_text())
        cls.report = json.loads((FROZEN / "out/CANDIDATE.json").read_text())

    def test_frozen_report_reconstructs_safety_failure(self):
        result = audit_top_level(self.fixture, self.events, self.report)
        self.assertEqual(result["status"], "PASS_TOP_LEVEL_AUDIT")
        self.assertEqual(result["expected"]["decision"], "FAIL_SAFETY")
        self.assertIs(result["expected"]["mechanism_attribution_eligible"], False)

    def test_rejects_descriptive_decision_after_safety_violation(self):
        report = copy.deepcopy(self.report)
        report["decision"] = "DESCRIPTIVE_ALL_OFFER_TOTAL"
        self.assertEqual(audit_top_level(self.fixture, self.events, report)["mismatches"],
                         ["decision"])

    def test_rejects_mechanism_eligibility_after_safety_violation(self):
        report = copy.deepcopy(self.report)
        report["mechanism_attribution_eligible"] = True
        self.assertEqual(
            audit_top_level(self.fixture, self.events, report)["mismatches"],
            ["mechanism_attribution_eligible"],
        )

    def test_reproduces_v1_blind_spot_and_catches_it_in_successor_audit(self):
        report = copy.deepcopy(self.report)
        report["decision"] = "DESCRIPTIVE_ALL_OFFER_TOTAL"
        report["mechanism_attribution_eligible"] = True
        original = audit_frozen_v1(self.fixture, self.events, report)
        successor = audit_top_level(self.fixture, self.events, report)
        self.assertEqual(original["status"], "PASS_AUDIT")
        self.assertEqual(successor["status"], "FAIL_TOP_LEVEL_AUDIT")
        self.assertEqual(set(successor["mismatches"]),
                         {"decision", "mechanism_attribution_eligible"})


if __name__ == "__main__":
    unittest.main()
