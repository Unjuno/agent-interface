import copy
import json
import unittest

from audit import core_errors, verify
from candidate import run


class RepresentationContrastTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open("fixture.json", encoding="utf-8") as stream:
            cls.fixture = json.load(stream)
        cls.raw = run(cls.fixture)

    def test_exact_roster_and_visual_parity(self):
        self.assertEqual(len(self.raw["cases"]), 6)
        self.assertEqual([x["id"] for x in self.raw["cases"]], [
            "spreadsheet:none", "spreadsheet:spreadsheet_increment_A2", "spreadsheet:pixel_patch",
            "drawing:none", "drawing:drawing_replace_title", "drawing:pixel_patch"])
        for row in self.raw["cases"]:
            left = row["routes"]["flat"]["initial"]["render"]
            right = row["routes"]["structured"]["initial"]["render"]
            self.assertEqual(left, right)

    def test_representation_is_operationally_distinct(self):
        sheet = self.raw["cases"][0]["routes"]
        self.assertIn("formula", sheet["structured"]["initial"]["state"])
        self.assertNotIn("formula", sheet["flat"]["initial"]["state"])
        drawing = self.raw["cases"][3]["routes"]
        self.assertIn("elements", drawing["structured"]["initial"]["state"])
        self.assertIn("raster", drawing["flat"]["initial"]["state"])
        self.assertNotIn("elements", drawing["flat"]["initial"]["state"])

    def test_structural_effects_fail_closed_for_flat(self):
        self.assertEqual(self.raw["cases"][1]["routes"]["flat"]["post"]["status"], "UNKNOWN")
        self.assertEqual(self.raw["cases"][1]["routes"]["structured"]["post"]["state"]["cells"]["TOTAL"], 6)
        self.assertEqual(self.raw["cases"][4]["routes"]["flat"]["post"]["status"], "UNKNOWN")
        self.assertEqual(self.raw["cases"][4]["routes"]["structured"]["post"]["state"]["elements"]["title"], "BETA")

    def test_pixel_control_preserves_flat_route_advantage(self):
        for row in (self.raw["cases"][2], self.raw["cases"][5]):
            self.assertEqual(row["routes"]["flat"]["post"]["status"], "COMPLETE")
            self.assertLess(row["routes"]["flat"]["cost"]["total"], row["routes"]["structured"]["cost"]["total"])

    def test_cost_mixture_and_all_mutations(self):
        outcome = verify(self.raw, self.fixture)
        self.assertEqual(outcome["errors"], [])
        self.assertEqual(outcome["mutation_controls_rejected"], 7)
        self.assertEqual(outcome["mutation_controls_total"], 7)
        self.assertEqual(outcome["weighted_cost_units"], {
            "spreadsheet": {"flat": 4.8, "structured": 4.2},
            "drawing": {"flat": 4.4, "structured": 4.2}})

    def test_oracle_answer_injection_is_rejected(self):
        mutant = copy.deepcopy(self.raw)
        mutant["cases"][1]["routes"]["flat"]["post"]["state"]["pixels"]["TOTAL"] = 6
        self.assertTrue(core_errors(mutant, self.fixture))


if __name__ == "__main__":
    unittest.main()
