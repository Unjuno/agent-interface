import unittest

from audit_only_a06 import reconstruct, threshold


class PrefixReconstructionTests(unittest.TestCase):
    def test_interval_contains_nominal_ttc_for_exact_constant_velocity(self):
        history = [
            {"t_s": 0.0, "radius_px": 10.0, "bound_px": 0.5, "track_id": "x"},
            {"t_s": 1.0, "radius_px": 12.0, "bound_px": 0.5, "track_id": "x"},
            {"t_s": 2.0, "radius_px": 14.0, "bound_px": 0.5, "track_id": "x"},
        ]
        point, interval = reconstruct(history)
        self.assertAlmostEqual(point, 7.0)
        self.assertLessEqual(interval[0], 7.0)
        self.assertGreaterEqual(interval[1], 7.0)

    def test_nonmonotone_time_fails_closed(self):
        history = [
            {"t_s": 1.0, "radius_px": 10.0, "bound_px": 0.5, "track_id": "x"},
            {"t_s": 1.0, "radius_px": 11.0, "bound_px": 0.5, "track_id": "x"},
        ]
        self.assertEqual(reconstruct(history), (None, None))

    def test_track_identity_change_fails_closed(self):
        history = [
            {"t_s": 0.0, "radius_px": 10.0, "bound_px": 0.5, "track_id": "x"},
            {"t_s": 1.0, "radius_px": 11.0, "bound_px": 0.5, "track_id": "y"},
        ]
        self.assertEqual(reconstruct(history), (None, None))


class ThresholdTests(unittest.TestCase):
    def test_uses_calibration_controls_and_largest_zero_false_cut(self):
        rows = [
            {"id": "cal-control", "estimates": [{"point_ttc_s": 3.0}]},
            {"id": "eval-hazard", "estimates": [{"point_ttc_s": 0.1}]},
        ]
        labels = {
            "cal-control": {"split": "calibration", "hazard": False},
            "eval-hazard": {"split": "evaluation", "hazard": True},
        }
        self.assertEqual(threshold(rows, labels, "point"), 2.0)


if __name__ == "__main__":
    unittest.main()
