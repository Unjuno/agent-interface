"""Behavior tests for finite principal-stratum compatibility bounds."""

import json
import importlib.util
import unittest
from fractions import Fraction
from pathlib import Path


ROOT = Path(__file__).resolve().parent


class PrincipalStratumCandidateTests(unittest.TestCase):
    def test_exact_margins_separate_selected_demanders_from_always_demand(self):
        self.assertIsNotNone(importlib.util.find_spec("candidate"), "candidate.py is not implemented")
        import candidate

        fixture = json.loads((ROOT / "input.json").read_text(encoding="utf-8"))
        result = candidate.run(fixture)
        rows = {row["id"]: row for row in result["rows"]}

        selected = rows["asymmetric_selection"]["policies"]["p0"]
        self.assertEqual("-1/3", selected["observed_demand_contrast"])
        self.assertEqual("BOUNDED", selected["identification"])
        self.assertEqual("-1", selected["always_demand_bounds"]["lower"])
        self.assertEqual("1", selected["always_demand_bounds"]["upper"])
        self.assertEqual(1, selected["always_demand_size_min"])
        self.assertEqual(1, selected["always_demand_size_max"])
        self.assertTrue(selected["opposite_sign_completion_exists"])

        equal = rows["equal_demand_point"]["policies"]["p0"]
        self.assertEqual("POINT_IDENTIFIED", equal["identification"])
        self.assertEqual("1", equal["always_demand_bounds"]["lower"])
        self.assertEqual("1", equal["always_demand_bounds"]["upper"])

        empty = rows["empty_always_compatible"]["policies"]["p0"]
        self.assertEqual("UNIDENTIFIED_EMPTY_STRATUM", empty["identification"])
        self.assertTrue(empty["empty_always_compatible"])
        self.assertEqual("1", empty["always_demand_bounds"]["lower"])
        self.assertEqual("1", empty["always_demand_bounds"]["upper"])

        no_demand = rows["no_p0_demand"]["policies"]["p0"]
        self.assertEqual("UNIDENTIFIED_EMPTY_STRATUM", no_demand["identification"])
        self.assertIsNone(no_demand["always_demand_bounds"])
        self.assertTrue(no_demand["empty_always_compatible"])


if __name__ == "__main__":
    unittest.main()
