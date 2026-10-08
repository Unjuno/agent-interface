from fractions import Fraction
import unittest

import candidate
import build_cases
import audit


CARDINAL4 = [(1, 0), (0, 1), (-1, 0), (0, -1)]
EIGHTWAY8 = [(1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1), (0, -1), (1, -1)]


class SuccessorConstructionTests(unittest.TestCase):
    def test_public_matrix_has_frozen_all_offer_denominator(self):
        cases = build_cases.build_cases()
        self.assertEqual(len(cases["requests"]), 5379)
        self.assertEqual(sum(r["request_id"].startswith("primary/") for r in cases["requests"]), 5376)
        self.assertEqual(len({r["request_id"] for r in cases["requests"]}), 5379)

    def test_raw_auditor_rejects_omitted_release_receipt(self):
        request = next(r for r in build_cases.build_cases()["requests"] if r["request_id"].startswith("primary/") and r["policy"] == "horizon_nearest" and r["intent"] != [0, 0, 1])
        raw = {"request_id": request["request_id"], **candidate.compile_request(request)}
        self.assertEqual(audit.validate_row(request, raw), [])
        raw["release_receipt"] = {"after_slot": raw["executed_slots"], "all_inputs_up": False}
        self.assertEqual(audit.validate_row(request, raw), ["release_receipt"])

    def test_held_out_acceleration_collision_is_not_admitted_as_linear_transfer(self):
        cases = build_cases.build_cases()
        requests = {r["request_id"]: r for r in cases["requests"]}
        source_id = "primary/eightway8/shallow-positive/8/error_carry/6101"
        source = requests[source_id]
        raw = {"request_id": source_id, **candidate.compile_request(source)}
        truth = {
            "held_out_transfer_control": {
                "source_request_id": source_id,
                "dynamics": "velocity_next = velocity_previous + command; position_next = position_previous + velocity_next",
                "wall_x": 5,
                "classification": "HOLD_TRANSFER_UNSUPPORTED",
                "included_in_primary_metric": False,
            }
        }
        control = audit._transfer_control(requests, [raw], truth)
        self.assertTrue(control["collision"])
        self.assertEqual(control["classification"], "HOLD_TRANSFER_UNSUPPORTED")

    def test_euclidean_nearest_includes_diagonal_command_norm(self):
        # Dot-product-only selection incorrectly chooses NE here.
        self.assertEqual(candidate.nearest_action((Fraction(1), Fraction(1, 3)), EIGHTWAY8), (1, 0))
        request = {
            "intent": [3, 1, 3], "alphabet": EIGHTWAY8, "horizon": 1,
            "deadline_slots": 1, "max_abs_prefix_error": 1,
            "policy": "horizon_nearest", "seed": 0,
            "calibration_id": "linear-v1", "current_calibration_id": "linear-v1",
            "required_combo": None, "available_combos": ["E", "NE", "N", "NW", "W", "SW", "S", "SE"],
        }
        audited = audit.expected_result(request)
        self.assertEqual(audited["commands"], [[1, 0]])

    def test_error_carry_minimizes_exact_cumulative_prefix_error(self):
        self.assertEqual(
            candidate.error_carry_schedule((Fraction(3, 4), Fraction(1, 4)), 4, CARDINAL4),
            [(1, 0), (1, 0), (0, 1), (1, 0)],
        )

    def test_independent_rounding_is_reproducible_but_not_a_constant_nearest_arm(self):
        intent = (Fraction(3, 4), Fraction(1, 4))
        a = candidate.independent_round_schedule(intent, 16, CARDINAL4, seed=19)
        b = candidate.independent_round_schedule(intent, 16, CARDINAL4, seed=19)
        c = candidate.independent_round_schedule(intent, 16, CARDINAL4, seed=23)
        self.assertEqual(a, b)
        self.assertNotEqual(a, c)

    def test_unavailable_required_combination_refuses_without_press(self):
        result = candidate.compile_request({
            "intent": [1, 1, 2], "horizon": 4, "deadline_slots": 4,
            "alphabet": CARDINAL4, "required_combo": "NE",
            "available_combos": ["E", "N", "W", "S"],
            "calibration_id": "linear-v1", "current_calibration_id": "linear-v1",
        })
        self.assertEqual(result["disposition"], "REFUSE_UNAVAILABLE_COMBO")
        self.assertEqual(result["commands"], [])
        self.assertEqual(result["release_receipt"], {"after_slot": 0, "all_inputs_up": True})

    def test_deadline_shorter_than_frozen_horizon_refuses_without_extension(self):
        result = candidate.compile_request({
            "intent": [3, 1, 4], "horizon": 4, "deadline_slots": 1,
            "alphabet": CARDINAL4, "required_combo": None,
            "available_combos": ["E", "N", "W", "S"],
            "calibration_id": "linear-v1", "current_calibration_id": "linear-v1",
        })
        self.assertEqual(result["disposition"], "REFUSE_DEADLINE")
        self.assertEqual(result["commands"], [])
        self.assertEqual(result["release_receipt"], {"after_slot": 0, "all_inputs_up": True})

    def test_calibration_mismatch_refuses_without_press(self):
        result = candidate.compile_request({
            "intent": [3, 1, 4], "horizon": 4, "deadline_slots": 4,
            "alphabet": CARDINAL4, "required_combo": None,
            "available_combos": ["E", "N", "W", "S"],
            "calibration_id": "linear-v1", "current_calibration_id": "linear-v2",
        })
        self.assertEqual(result["disposition"], "REFUSE_CALIBRATION_MISMATCH")
        self.assertEqual(result["commands"], [])
        self.assertEqual(result["release_receipt"], {"after_slot": 0, "all_inputs_up": True})


if __name__ == "__main__":
    unittest.main()
