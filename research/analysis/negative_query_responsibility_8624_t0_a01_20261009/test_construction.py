#!/usr/bin/env python3
"""Construction checks; not the frozen candidate or auditor invocation."""
import copy
import json
import unittest
from pathlib import Path

from candidate import analyze


ROOT = Path(__file__).resolve().parent


class CandidateConstruction(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.packet = json.loads((ROOT / "input.json").read_text())
        cls.cases = {case["id"]: case for case in cls.packet["cases"]}

    def row(self, name):
        return analyze(self.cases[name], self.packet["max_worlds"])

    def test_monotone_positive_control(self):
        row = self.row("monotone_positive_control")
        self.assertEqual(row["outcome"], "MATCH")
        self.assertEqual(row["minimal_positive_match_supports"],
                         [sorted(self.cases["monotone_positive_control"]["facts"])])
        self.assertEqual(row["actual_causes"], {})

    def test_absent_prerequisite_and_present_exception_are_signed(self):
        missing = self.row("absent_prerequisite")
        blocker = self.row("present_exception")
        self.assertEqual(missing["outcome"], "NO_MATCH")
        self.assertEqual(missing["actual_causes"]["candidate"]["literal"], False)
        self.assertEqual(missing["actual_causes"]["candidate"]["minimum_contingency"], 0)
        self.assertEqual(blocker["outcome"], "NO_MATCH")
        self.assertEqual(blocker["actual_causes"]["modal"]["literal"], True)
        self.assertEqual(blocker["actual_causes"]["modal"]["minimum_contingency"], 0)

    def test_contingency_only_cause_and_separate_global_radius(self):
        row = self.row("contingency_only_exception")
        self.assertEqual(row["outcome"], "NO_MATCH")
        self.assertEqual(row["actual_causes"]["exception"]["minimum_contingency"], 2)
        self.assertNotIn("exception", row["positive_eligibility_supports"])
        row2 = self.row("robustness_vs_contingency")
        self.assertEqual(row2["robustness_radius"], 1)
        self.assertEqual(row2["actual_causes"]["exception"]["minimum_contingency"], 2)

    def test_identical_positive_summary_does_not_identify_negation(self):
        a = self.row("same_positive_support_no_exception")
        b = self.row("same_positive_support_with_exception")
        self.assertEqual(a["positive_eligibility_supports"], b["positive_eligibility_supports"])
        self.assertNotEqual(a["minimal_positive_match_supports"],
                            b["minimal_positive_match_supports"])
        self.assertEqual((a["outcome"], b["outcome"]), ("MATCH", "NO_MATCH"))

    def test_budget_and_incomplete_scope_fail_closed(self):
        dense = self.row("dense_budget_control")
        incomplete = self.row("incomplete_scope_control")
        self.assertEqual(dense["status"], "UNKNOWN_TOO_LARGE")
        self.assertFalse(dense["explanation_complete"])
        self.assertEqual(incomplete["status"], "UNKNOWN_INCOMPLETE")
        self.assertEqual(incomplete["outcome"], "UNKNOWN")

    def test_polarity_mutation_changes_outcome(self):
        case = copy.deepcopy(self.cases["present_exception"])
        before = analyze(case, self.packet["max_worlds"])
        case["facts"]["modal"] = False
        after = analyze(case, self.packet["max_worlds"])
        self.assertEqual((before["outcome"], after["outcome"]), ("NO_MATCH", "MATCH"))

    def test_intervention_domain_and_omitted_fact_mutations_reject(self):
        extra = copy.deepcopy(self.cases["present_exception"])
        extra["facts"]["fixed_policy"] = False
        extra["fact_universe"].append("fixed_policy")
        extra["mutable"].append("fixed_policy")
        with self.assertRaises(ValueError):
            analyze(extra, self.packet["max_worlds"])
        omitted = copy.deepcopy(self.cases["absent_prerequisite"])
        omitted["mutable"].remove("candidate")
        with self.assertRaises(ValueError):
            analyze(omitted, self.packet["max_worlds"])

    def test_stratum_and_endpoint_mutations_reject(self):
        reordered = copy.deepcopy(self.cases["present_exception"])
        next(rule for rule in reordered["rules"] if rule["head"] == "primary")["stratum"] = 0
        with self.assertRaises(ValueError):
            analyze(reordered, self.packet["max_worlds"])
        changed_endpoint = copy.deepcopy(self.cases["present_exception"])
        changed_endpoint["endpoint"] = "eligible"
        with self.assertRaises(ValueError):
            analyze(changed_endpoint, self.packet["max_worlds"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
