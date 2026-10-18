import unittest
from fractions import Fraction as F

from candidate import evaluate


def base_case(**updates):
    case = {
        "id": "test",
        "current": [["1/5", "0"], ["0", "1/5"]],
        "delayed": [["0", "0"], ["0", "0"]],
        "actuator": [["1/5", "0"], ["0", "1/5"]],
        "controller": [["1", "0"], ["0", "1"]],
        "release": [["0", "0"], ["0", "0"]],
        "release_factor": ["0", "0"],
        "delay_schedule": [0, 1, 0, 1],
        "estimator_error": ["0", "0"],
        "disturbance": ["0", "0"],
        "saturation": ["4", "4"],
        "hold_requested": [1, 1],
        "hold_limit": [2, 2],
        "initial": ["1", "1"],
        "feature_limit": "2",
        "horizon": 4,
    }
    case.update(updates)
    return case


class CandidateContractTests(unittest.TestCase):
    def test_uncoupled_contraction_is_certified(self):
        self.assertEqual(evaluate(base_case())["disposition"], "CERTIFIED")

    def test_cross_axis_coupling_is_included_in_gain_screen(self):
        case = base_case(
            current=[["1/2", "0"], ["0", "1/2"]],
            actuator=[["0", "3/4"], ["3/4", "0"]],
            saturation=["4", "4"], hold_requested=[1, 1], hold_limit=[2, 2],
            feature_limit="2", horizon=8,
        )
        result = evaluate(case)
        self.assertEqual(result["disposition"], "NO_COMPOSITION_CERTIFICATE")
        self.assertEqual(result["gain_matrix"], [["1/2", "3/4"], ["3/4", "1/2"]])
        self.assertTrue(all(result["subsystem_checks"].values()))
        self.assertEqual(result["gain_envelope_status"], "UNSTABLE_ENVELOPE")

    def test_unit_gain_boundary_is_not_called_unstable(self):
        case = base_case(
            current=[["1/2", "0"], ["0", "1/2"]],
            actuator=[["0", "1/2"], ["1/2", "0"]],
        )
        self.assertEqual(evaluate(case)["gain_envelope_status"], "BOUNDED_NONCONVERGENT_ENVELOPE")

    def test_overlong_input_hold_cannot_be_certified(self):
        case = base_case(hold_requested=[3, 1], hold_limit=[2, 2])
        self.assertEqual(evaluate(case)["disposition"], "NO_COMPOSITION_CERTIFICATE")

    def test_admitted_hold_duration_scales_actuator_effect(self):
        short = evaluate(base_case(hold_requested=[1, 1]))
        long = evaluate(base_case(hold_requested=[2, 2]))
        self.assertGreater(F(long["trajectory"][1][0]), F(short["trajectory"][1][0]))

    def test_release_path_contributes_to_composed_gain(self):
        case = base_case(
            release=[["3", "0"], ["0", "3"]], release_factor=["1", "1"],
            current=[["1/5", "0"], ["0", "1/5"]],
            actuator=[["1/5", "0"], ["0", "1/5"]],
        )
        result = evaluate(case)
        self.assertGreaterEqual(F(result["gain_matrix"][0][0]), F(1))
        self.assertEqual(result["disposition"], "NO_COMPOSITION_CERTIFICATE")


if __name__ == "__main__":
    unittest.main()
