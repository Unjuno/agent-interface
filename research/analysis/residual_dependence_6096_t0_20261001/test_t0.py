import importlib.util
import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).parent
spec = importlib.util.spec_from_file_location("candidate", ROOT / "candidate.py")
candidate = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = candidate
spec.loader.exec_module(candidate)
PUBLIC = json.loads((ROOT / "public.json").read_text(encoding="utf-8"))
CASES = {case["id"]: case for case in PUBLIC["cases"]}
THRESHOLD = candidate.calibrate_threshold(PUBLIC)


class ResidualSentinelConstructionTests(unittest.TestCase):
    def test_training_only_calibration_includes_valid_periodic_bound(self):
        self.assertEqual(THRESHOLD, 4)

    def test_pointwise_and_mean_baselines_miss_subthreshold_zero_mean_trace(self):
        danger = CASES["heldout-phase-lag-danger"]
        self.assertEqual(candidate.decide(PUBLIC, danger, "pointwise", THRESHOLD)["stop_reason"], "CONTINUE_TO_HORIZON")
        self.assertEqual(candidate.decide(PUBLIC, danger, "running_mean", THRESHOLD)["stop_reason"], "CONTINUE_TO_HORIZON")

    def test_calibrated_sentinel_respects_training_false_alarm_bound(self):
        training_periodic = PUBLIC["training"][2]["residual_num"]
        self.assertEqual(max(0, candidate.lag_sum(training_periodic, PUBLIC["dependence_window_pairs"])), 3)
        self.assertGreaterEqual(THRESHOLD, 4)

    def test_lower_threshold_detects_danger_but_trips_indistinguishable_valid_prefix(self):
        danger = CASES["heldout-phase-lag-danger"]
        valid = CASES["heldout-valid-periodic"]
        jitter = CASES["heldout-camera-jitter"]
        for case in (danger, valid, jitter):
            result = candidate.decide(PUBLIC, case, "calibrated_dependence", 3)
            self.assertEqual(result["seen_samples"], 6)
            self.assertEqual(result["stop_reason"], "YIELD_DEPENDENCE")
        self.assertEqual(danger["residual_num"][:6], valid["residual_num"][:6])
        self.assertEqual(danger["residual_num"][:6], jitter["residual_num"][:6])

    def test_mean_shift_positive_control_is_detected(self):
        result = candidate.decide(PUBLIC, CASES["mean-shift-positive"], "running_mean", THRESHOLD)
        self.assertEqual(result["stop_reason"], "YIELD_RUNNING_MEAN")
        self.assertEqual(result["seen_samples"], 1)

    def test_identity_and_missing_evidence_fail_closed(self):
        changed = candidate.decide(PUBLIC, CASES["target-identity-swap"], "calibrated_dependence", THRESHOLD)
        missing = candidate.decide(PUBLIC, CASES["missing-observation"], "calibrated_dependence", THRESHOLD)
        self.assertEqual((changed["seen_samples"], changed["stop_reason"]), (4, "YIELD_IDENTITY_CHANGE"))
        self.assertEqual((missing["seen_samples"], missing["stop_reason"]), (4, "YIELD_MISSING"))


if __name__ == "__main__":
    unittest.main()
