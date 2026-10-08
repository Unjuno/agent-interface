import copy
import json
import unittest
from pathlib import Path

import audit
import candidate

HERE = Path(__file__).resolve().parent
PUBLIC = json.loads((HERE / "cases_public.json").read_text(encoding="utf-8"))
TRUTH = json.loads((HERE / "oracle_truth.json").read_text(encoding="utf-8"))
COSTS = json.loads((HERE / "costs.json").read_text(encoding="utf-8"))


class ArtifactChangeabilityTests(unittest.TestCase):
    def setUp(self):
        self.raw = candidate.run(PUBLIC["cases"])

    def test_all_six_cases_have_both_routes_and_initial_parity(self):
        result = audit.audit(PUBLIC, TRUTH, COSTS, self.raw)
        self.assertEqual(result["status"], "METHOD_PASS_SCOPED", result)
        self.assertEqual(result["rows"], 12)

    def test_flat_sheet_reconstructs_only_when_later_request_needs_formula(self):
        row = next(x for x in self.raw if x["case_id"] == "sheet_no_followup" and x["route"] == "flat")
        self.assertIsNone(row["artifact"]["formula"])
        row = next(x for x in self.raw if x["case_id"] == "sheet_formula_rebuild" and x["route"] == "flat")
        self.assertEqual(row["artifact"]["formula"], "SUM(A,B)")
        self.assertEqual(row["final_visible"], [4, 4, 8])

    def test_raster_yields_when_occluded_underlay_is_required(self):
        row = next(x for x in self.raw if x["case_id"] == "drawing_move_preserve_underlay" and x["route"] == "raster")
        self.assertEqual(row["outcome"], "UNKNOWN_UNDERLAY_NOT_RETAINED")
        self.assertIsNone(row["final_visible"])

    def test_native_move_preserves_underlay(self):
        row = next(x for x in self.raw if x["case_id"] == "drawing_move_preserve_underlay" and x["route"] == "native")
        self.assertEqual(row["final_visible"], [["white", "red", "blue", "green"]])

    def test_answer_injection_does_not_change_candidate(self):
        mutated = copy.deepcopy(PUBLIC["cases"])
        for case in mutated:
            case["expected_total"] = 999
        self.assertEqual(candidate.run(mutated), self.raw)

    def test_corruption_controls_are_rejected(self):
        mutations = []
        x = copy.deepcopy(self.raw); next(r for r in x if r["case_id"] == "sheet_formula_rebuild" and r["route"] == "flat")["artifact"]["formula"] = "A+B+99"; mutations.append(x)
        x = copy.deepcopy(self.raw); next(r for r in x if r["case_id"] == "drawing_move_preserve_underlay" and r["route"] == "native")["final_visible"][0][1] = "white"; mutations.append(x)
        x = copy.deepcopy(self.raw); next(r for r in x if r["case_id"] == "drawing_move_preserve_underlay" and r["route"] == "native")["artifact"]["objects"].pop(0); mutations.append(x)
        x = copy.deepcopy(self.raw); next(r for r in x if r["case_id"] == "drawing_move_preserve_underlay" and r["route"] == "native")["artifact"]["objects"][0]["id"] = "wrong-target"; mutations.append(x)
        x = copy.deepcopy(self.raw); next(r for r in x if r["case_id"] == "drawing_no_followup" and r["route"] == "raster")["artifact"]["objects"] = TRUTH["drawing_layers"]; mutations.append(x)
        x = copy.deepcopy(self.raw); x.pop(); mutations.append(x)
        x = copy.deepcopy(self.raw); next(r for r in x if r["case_id"] == "sheet_pixel_style" and r["route"] == "structured")["artifact"]["B"] = 77; mutations.append(x)
        self.assertEqual(len(mutations), 7)
        for corrupted in mutations:
            with self.subTest(corruption=len(corrupted)):
                self.assertEqual(audit.audit(PUBLIC, TRUTH, COSTS, corrupted)["status"], "FAIL_AUDIT")


if __name__ == "__main__":
    unittest.main(verbosity=2)
