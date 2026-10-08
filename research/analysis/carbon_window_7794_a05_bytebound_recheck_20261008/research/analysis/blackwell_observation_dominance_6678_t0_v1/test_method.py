import unittest
from fractions import Fraction
import copy

import auditor
import candidate
from fixture_loader import fixture


class BlackwellT0Tests(unittest.TestCase):
    def test_known_garbling_and_reverse_control(self):
        rows = candidate.run(fixture)["relations"]
        self.assertTrue(rows["fine>=partition_s0"]["feasible"])
        self.assertFalse(rows["partition_s0>=fine"]["feasible"])
        self.assertTrue(rows["partition_s0>=uninformative"]["feasible"])

    def test_incomparable_pair_and_decision_dependent_ranking(self):
        result = auditor.audit(fixture, candidate.run(fixture))
        self.assertEqual(result["verdict"], "METHOD_PASS_SCOPED")
        risks = result["risks"]
        self.assertLess(Fraction(*risks["focus_s0"]["partition_s0"]), Fraction(*risks["focus_s0"]["partition_s2"]))
        self.assertLess(Fraction(*risks["focus_s2"]["partition_s2"]), Fraction(*risks["focus_s2"]["partition_s0"]))

    def test_certificate_mutation_is_rejected(self):
        raw = candidate.run(fixture)
        raw["relations"]["fine>=partition_s0"]["garbling"][0][0] = [0, 1]
        self.assertEqual(auditor.audit(fixture, raw)["verdict"], "FAIL_METHOD")

    def test_channel_identity_leak_mutation_is_rejected(self):
        raw = candidate.run(fixture)
        raw["observations"][0][0] = "fine"
        self.assertEqual(auditor.audit(fixture, raw)["verdict"], "FAIL_METHOD")

    def test_frozen_channel_mapping_mutation_is_rejected(self):
        changed = copy.deepcopy(fixture)
        changed["channels"]["partition_s0"]["kernel"][0][0] = [0, 1]
        self.assertEqual(auditor.audit(changed, candidate.run(fixture))["verdict"], "FAIL_METHOD")


if __name__ == "__main__":
    unittest.main()
