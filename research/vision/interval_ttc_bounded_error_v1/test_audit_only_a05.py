import importlib.util
import pathlib
import unittest


MODULE_PATH = pathlib.Path(__file__).with_name("audit_only_a05.py")
SPEC = importlib.util.spec_from_file_location("audit_only_a05", MODULE_PATH)
audit = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(audit)


class RetainedRawScoreAuditTests(unittest.TestCase):
    def test_prefix_estimator_uses_only_valid_expanding_history(self):
        history = [
            {"t_s": 0.0, "radius_px": 10.0, "bound_px": 0.5, "track_id": "a"},
            {"t_s": 1.0, "radius_px": 12.0, "bound_px": 0.5, "track_id": "a"},
        ]
        point, interval = audit.estimate_prefix(history)
        self.assertEqual(point, 6.0)
        self.assertEqual(interval, (11.5 / 3.0, 12.5 / 1.0))
        invalid = history + [
            {"t_s": 2.0, "radius_px": 13.0, "bound_px": 0.5, "track_id": "b"}
        ]
        self.assertEqual(audit.estimate_prefix(invalid), (None, None))

    def test_score_keeps_no_yield_result_as_diagnostic_not_formal_pass(self):
        profiles = ["approach", "passby", "stationary", "iid", "correlated",
                    "irregular_dropout", "acceleration", "occlusion",
                    "identity_swap", "understated_bound"]
        oracle, candidate = [], []
        for profile in profiles:
            for ordinal in range(20):
                sid = f"{profile}-{ordinal}"
                hazard = ordinal % 2 == 0
                oracle.append({
                    "id": sid, "profile": profile, "hazard": hazard,
                    "eligible_in_model": profile in audit.IN_MODEL_PROFILES and hazard,
                    "split": "calibration" if ordinal % 2 == 0 else "evaluation",
                    "truth": [{"observed": True, "true_ttc_s": 3.0}],
                })
                candidate.append({"id": sid, "estimates": [{
                    "point_ttc_s": None, "interval_s": None,
                }]})
        result = audit.score([], oracle, candidate)
        self.assertEqual(result["formal_a02_disposition"], "FAIL_METHOD_UNSCORABLE_PRESERVED")
        self.assertEqual(result["diagnostic_disposition"], "MIXED_OR_INCOMPLETE_DIAGNOSTIC")
        self.assertEqual(result["thresholds_s"], {"point": 2.0, "interval": 2.0})

    def test_row_set_mismatch_is_rejected(self):
        self.assertEqual(
            audit.reconstruction_errors([], [], []), ["row_count_or_ids"]
        )


if __name__ == "__main__":
    unittest.main()
