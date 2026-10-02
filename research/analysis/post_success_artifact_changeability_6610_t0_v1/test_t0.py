import copy
import json
import unittest

from candidate import run_case
from audit import verify, verify_core


class AssayTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open("fixture.json", encoding="utf-8") as f:
            cls.fixture = json.load(f)
        cls.raw = {"schema": "post-success-changeability-raw-v1", "fixture_schema": cls.fixture["schema"],
                   "cases": [run_case(case, cls.fixture) for case in cls.fixture["cases"]]}

    def test_six_declared_cases_and_initial_equivalence(self):
        self.assertEqual(len(self.raw["cases"]), 6)
        for row in self.raw["cases"]:
            self.assertEqual(row["routes"]["flat"]["initial"]["render"], row["routes"]["structured"]["initial"]["render"])
            self.assertTrue(row["routes"]["flat"]["initial"]["pass"])
            self.assertTrue(row["routes"]["structured"]["initial"]["pass"])

    def test_mixture_reverses_initial_ranking_both_families(self):
        errors, controls = verify(self.raw, self.fixture)
        self.assertEqual(errors, [])
        self.assertEqual(controls["controls_rejected"], 5)
        self.assertEqual(controls["controls_total"], 5)
        self.assertEqual(controls["cost_comparison"], [
            {"family": "spreadsheet", "initial_flat": 1, "initial_structured": 3,
             "mixture_expected_flat": 4.8, "mixture_expected_structured": 4.2,
             "no_followup_flat": 1, "no_followup_structured": 3,
             "raster_patch_flat": 2, "raster_patch_structured": 7},
            {"family": "drawing", "initial_flat": 1, "initial_structured": 3,
             "mixture_expected_flat": 4.4, "mixture_expected_structured": 4.2,
             "no_followup_flat": 1, "no_followup_structured": 3,
             "raster_patch_flat": 2, "raster_patch_structured": 7},
        ])

    def test_flat_preferred_when_no_change_or_raster_change(self):
        for family in ("spreadsheet", "drawing"):
            rows = [x for x in self.raw["cases"] if x["family"] == family]
            for row in (x for x in rows if x["followup"] == "none" or "raster_patch" in x["followup"]):
                self.assertLess(row["routes"]["flat"]["total_cost"], row["routes"]["structured"]["total_cost"])

    def test_structural_edits_preserve_unrelated_content(self):
        for row in self.raw["cases"]:
            if "structural" in row["followup"]:
                for route in ("flat", "structured"):
                    self.assertTrue(row["routes"][route]["post"]["pass"])

    def test_raw_corruptions_reject(self):
        errors, _ = verify(self.raw, self.fixture)
        self.assertFalse(errors)
        mutants = []
        m = copy.deepcopy(self.raw); m["cases"][0]["routes"]["flat"]["initial"]["pass"] = False; mutants.append(m)
        m = copy.deepcopy(self.raw); m["cases"][1]["routes"]["flat"]["post"]["state"]["untouched"]["B1"] = "CHANGED"; mutants.append(m)
        m = copy.deepcopy(self.raw); m["cases"][1]["routes"]["structured"]["post"]["state"]["formula"] = "=SUM(A1:B1)"; mutants.append(m)
        m = copy.deepcopy(self.raw); m["cases"][1]["routes"]["flat"]["initial"]["state"]["native_element_ids"] = ["title"]; mutants.append(m)
        self.assertTrue(all(verify_core(m, self.fixture) for m in mutants))
        stricter = copy.deepcopy(self.fixture); stricter["initial_contract"]["spreadsheet"]["required_structure"] = "formula"
        self.assertTrue(verify_core(self.raw, stricter))


if __name__ == "__main__":
    unittest.main()
