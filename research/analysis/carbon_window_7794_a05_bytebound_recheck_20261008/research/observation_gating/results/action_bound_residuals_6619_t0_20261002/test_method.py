import unittest

import candidate
import make_fixture


class ActionBoundResidualConstructionTests(unittest.TestCase):
    def case(self, name, dx, **kwargs):
        return make_fixture.build_case(name, dx, **kwargs)[0]

    def test_valid_pan_is_explained_without_erasing_independent_flash(self):
        clean = candidate.analyze_case(self.case("clean", 2, support=[2]))
        flash = candidate.analyze_case(self.case("flash", 2, support=[2], event="flash"))
        self.assertTrue(clean["methods"]["raw_delta"]["alarm"])
        self.assertFalse(clean["methods"]["action_bound"]["alarm"])
        self.assertTrue(flash["methods"]["action_bound"]["alarm"])
        self.assertEqual(len(flash["methods"]["action_bound"]["residual_indices"]), 1)

    def test_receipt_mismatch_falls_back_to_full_frame(self):
        case = self.case("late", 2, support=[2], ack_ns=350_000, event="flash")
        result = candidate.analyze_case(case)["methods"]["action_bound"]
        self.assertEqual(result["fallback"], "UNKNOWN_FULL_FRAME")
        self.assertEqual(result["binding"], "receipt_not_current_at_capture")
        self.assertTrue(result["alarm"])

    def test_critical_pixels_remain_a_hard_parallel_cue(self):
        case = self.case("critical", 2, support=[2], event="critical_cue")
        result = candidate.analyze_case(case)["methods"]["action_bound"]
        self.assertTrue(result["alarm"])
        self.assertEqual(result["critical_delta_indices"], [2 * make_fixture.WIDTH + 15])

    def test_foreign_intent_sham_is_not_used_to_explain_pan(self):
        case = self.case("sham", 2, support=[2])
        result = candidate.analyze_case(case)["methods"]["sham_bound"]
        self.assertEqual(result["fallback"], "UNKNOWN_FULL_FRAME")
        self.assertEqual(result["binding"], "intent_mismatch")

    def test_unmodelled_motion_stays_visible_as_residual(self):
        case = self.case("parallax", 2, support=[2], variant="parallax")
        result = candidate.analyze_case(case)["methods"]["action_bound"]
        self.assertGreater(len(result["residual_indices"]), 0)
        self.assertTrue(result["alarm"])


if __name__ == "__main__":
    unittest.main()
