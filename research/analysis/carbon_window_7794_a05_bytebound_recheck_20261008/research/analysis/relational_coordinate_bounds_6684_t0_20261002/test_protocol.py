from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

import auditor
import candidate


ROOT = Path(__file__).parent
DESIGN = json.loads((ROOT / "design.json").read_text())


class RelationalCoordinateBoundsTests(unittest.TestCase):
    def test_fixture_world_counts_fit_bounded_construction_budget(self):
        counts = {}
        for case in DESIGN["cases"]:
            shift_names = {case[key]["shift_var"] for key in ("target", "action", "forbidden")}
            shifts = 1
            for name in shift_names:
                domain = DESIGN["shift_variables"][name]
                shifts *= (domain["x"][1] - domain["x"][0] + 1) * (domain["y"][1] - domain["y"][0] + 1)
            errors = 1
            for key in ("target", "action", "forbidden"):
                for lo, hi in case[key]["error"]:
                    errors *= hi - lo + 1
            counts[case["case_id"]] = shifts * errors * len(case["scale_values"])
        self.assertLessEqual(max(counts.values()), 100_000, counts)

    def test_relational_bounds_reduce_common_mode_false_unknown_without_false_admit(self):
        raw = candidate.run(DESIGN)
        result = auditor.audit(DESIGN, raw)
        self.assertEqual(result["disposition"], "PASS_METHOD_SCOPED", result["errors"])
        summary = result["summary"]
        self.assertEqual(summary["common_mode_exact_safe_cases"], 3)
        self.assertEqual(summary["common_mode_BOX_false_unknown"], 3)
        self.assertEqual(summary["common_mode_RELATIONAL_false_unknown"], 0)
        self.assertEqual(summary["false_admissions"], 0)

    def test_independent_target_action_error_controls_show_no_advantage(self):
        raw = candidate.run(DESIGN)
        rows = {r["case_id"]: r for r in raw["rows"]}
        for case_id in ("INDEPENDENT_SAFE_NO_GAIN", "INDEPENDENT_UNSAFE_NO_GAIN",
                        "INDEPENDENT_FRAME_TRANSLATION_NO_GAIN"):
            self.assertEqual(rows[case_id]["BOX"]["decision"], rows[case_id]["RELATIONAL"]["decision"])

    def test_scale_boundary_collateral_and_large_independent_error_refuse(self):
        rows = {r["case_id"]: r for r in candidate.run(DESIGN)["rows"]}
        for case_id in ("CM_UNSAFE_SCALE_BOUNDARY", "CM_UNSAFE_ADJACENT_COLLATERAL",
                        "CM_UNSAFE_INDEPENDENT_MEASUREMENT_ERROR", "INDEPENDENT_UNSAFE_NO_GAIN"):
            self.assertEqual(rows[case_id]["RELATIONAL"]["decision"], "UNKNOWN_REOBSERVE", case_id)

    def test_bad_units_fail_closed(self):
        bad = copy.deepcopy(DESIGN)
        bad["coordinate_unit"] = "dp"
        self.assertTrue(all(not r["valid"] and r["RELATIONAL"]["decision"] == "UNKNOWN_REOBSERVE"
                            for r in candidate.run(bad)["rows"]))

    def test_frame_id_mismatch_fails_closed(self):
        case = copy.deepcopy(DESIGN["cases"][0])
        case["action"]["frame_id"] = "viewport-B"
        result = candidate.evaluate(case, DESIGN)
        self.assertFalse(result["valid"])
        self.assertEqual(result["RELATIONAL"]["reason"], "frame_id_mismatch")

    def test_stale_or_mixed_epoch_fails_closed(self):
        case = copy.deepcopy(DESIGN["cases"][0])
        case["action"]["epoch"] += 1
        result = candidate.evaluate(case, DESIGN)
        self.assertFalse(result["valid"])
        self.assertEqual(result["RELATIONAL"]["reason"], "stale_or_mixed_epoch")

    def test_target_identity_swap_fails_closed_without_selecting_neighbor(self):
        case = copy.deepcopy(DESIGN["cases"][0])
        case["action"]["target_id"] = case["forbidden"]["id"]
        result = candidate.evaluate(case, DESIGN)
        self.assertFalse(result["valid"])
        self.assertEqual(result["RELATIONAL"]["reason"], "target_identity_mismatch")

    def test_contradictory_shift_bounds_fail_closed(self):
        bad = copy.deepcopy(DESIGN)
        bad["shift_variables"]["shared"]["x"] = [2, -2]
        result = candidate.evaluate(bad["cases"][0], bad)
        self.assertFalse(result["valid"])
        self.assertEqual(result["RELATIONAL"]["reason"], "invalid_integer_interval")

    def test_auditor_rejects_relation_sign_mutation(self):
        raw = candidate.run(DESIGN)
        row = next(r for r in raw["rows"] if r["case_id"] == "CM_SAFE_SCALED_OFFSET")
        lo, hi = row["RELATIONAL"]["action_minus_target"][0]
        row["RELATIONAL"]["action_minus_target"][0] = [-hi, -lo]
        audit = auditor.audit(DESIGN, raw)
        self.assertNotEqual(audit["disposition"], "PASS_METHOD_SCOPED")
        self.assertTrue(any("under_approximation" in error for error in audit["errors"]))

    def test_auditor_rejects_false_admit(self):
        raw = candidate.run(DESIGN)
        row = next(r for r in raw["rows"] if r["case_id"] == "CM_UNSAFE_SCALE_BOUNDARY")
        row["RELATIONAL"]["decision"] = "ADMIT"
        audit = auditor.audit(DESIGN, raw)
        self.assertTrue(any("false_admit" in error for error in audit["errors"]))


if __name__ == "__main__":
    unittest.main()
