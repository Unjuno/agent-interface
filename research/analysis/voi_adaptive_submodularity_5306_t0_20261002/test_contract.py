from __future__ import annotations

import json
import unittest
from fractions import Fraction
from pathlib import Path

import audit
import candidate

ROOT = Path(__file__).resolve().parent
MODEL = json.loads((ROOT / "model.json").read_text(encoding="utf-8"))


class AdaptiveSubmodularityTests(unittest.TestCase):
    def test_complementary_checks_have_increasing_conditional_marginal(self):
        case = MODEL["cases"][0]
        checks = {c["id"]: c for c in case["checks"]}
        self.assertEqual(Fraction(0), candidate.marginal(case, {}, checks["B"]))
        self.assertEqual(Fraction(2, 45), candidate.marginal(case, {"A": "-"}, checks["B"]))

    def test_duplicate_negative_control_has_zero_followup_value(self):
        case = MODEL["cases"][1]
        checks = {c["id"]: c for c in case["checks"]}
        self.assertEqual(Fraction(1, 2), candidate.marginal(case, {}, checks["A_COPY"]))
        self.assertEqual(Fraction(0), candidate.marginal(case, {"A": "GOOD"}, checks["A_COPY"]))

    def test_greedy_stops_but_root_bellman_policy_is_strictly_better(self):
        case = MODEL["cases"][0]
        greedy = candidate.greedy_tree(case)
        exact = audit.combine(MODEL, case, {}, (), Fraction())
        self.assertEqual("STOP", greedy["action"])
        self.assertEqual("A", exact["action"])
        self.assertEqual("B", exact["branches"]["-"]["next"]["action"])
        self.assertEqual(Fraction(49, 7500), exact["net"] - Fraction(7, 10))

    def test_stale_and_infeasible_controls_yield_without_optional_calls(self):
        result = candidate.run(MODEL)
        self.assertEqual([("stale_source", "YIELD", 0), ("deadline_infeasible", "YIELD", 0)],
                         [(g["id"], g["disposition"], g["optional_calls"]) for g in result["gate_controls"]])

    def test_auditor_rejects_a_false_greedy_call_claim(self):
        output = candidate.run(MODEL)
        output["cases"]["complementary_no_singleton_voi"]["greedy_tree"]["action"] = "A"
        with self.assertRaises(AssertionError):
            audit.verify_candidate(MODEL, output)


if __name__ == "__main__":
    unittest.main()
