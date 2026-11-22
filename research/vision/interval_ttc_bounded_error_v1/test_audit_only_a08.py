import importlib.util
import pathlib
import unittest

MODULE = pathlib.Path(__file__).with_name("audit_only_a08.py")
SPEC = importlib.util.spec_from_file_location("audit_only_a08", MODULE)
audit = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(audit)


class A08AuditTests(unittest.TestCase):
    def test_causal_estimator_refuses_nonexpanding_or_changed_track(self):
        history = [
            {"t_s": 0.0, "radius_px": 10.0, "bound_px": .5, "track_id": "a"},
            {"t_s": 1.0, "radius_px": 12.0, "bound_px": .5, "track_id": "a"},
        ]
        point, interval = audit.estimate_prefix(history)
        self.assertEqual(point, 6.0)
        self.assertAlmostEqual(interval[0], 11.5 / 3.0)
        self.assertEqual(audit.estimate_prefix(history + [
            {"t_s": 2.0, "radius_px": 13.0, "bound_px": .5, "track_id": "b"}
        ]), (None, None))

    def test_profile_eligibility_flip_is_detected(self):
        profiles = sorted(audit.PROFILES)
        truth = []
        public = []
        candidate = []
        for profile in profiles:
            for ordinal in range(20):
                sid = f"{profile}-{ordinal}"
                hazard = ordinal % 2 == 0
                truth.append({"id": sid, "profile": profile, "hazard": hazard,
                              "eligible_in_model": profile in audit.IN_MODEL and hazard,
                              "split": "calibration" if ordinal < 10 else "evaluation",
                              "truth": [{"observed": True, "true_ttc_s": 1.0}]})
                public.append({"id": sid, "history": [{}]})
                candidate.append({"id": sid, "estimates": [{"point_ttc_s": None,
                                                               "interval_s": None}]})
        flipped = [dict(x) for x in truth]
        flipped[0]["eligible_in_model"] = not flipped[0]["eligible_in_model"]
        self.assertTrue(audit.validate_structure(public, flipped, candidate))

    def test_missing_interval_is_caught_by_independent_prefix_reconstruction(self):
        history = [
            {"t_s": 0.0, "radius_px": 10.0, "bound_px": .5, "track_id": "a"},
            {"t_s": 1.0, "radius_px": 12.0, "bound_px": .5, "track_id": "a"},
        ]
        point, interval = audit.estimate_prefix(history)
        public = [{"id": "x", "history": history}]
        candidate = [{"id": "x", "estimates": [
            {"point_ttc_s": None, "interval_s": None},
            {"point_ttc_s": point, "interval_s": interval},
        ]}]
        self.assertEqual(audit.reconstruction_errors(public, candidate), [])
        candidate[0]["estimates"][1]["interval_s"] = None
        self.assertTrue(audit.reconstruction_errors(public, candidate))

    def test_calibration_threshold_ignores_evaluation_controls_and_lead_gate_is_paired(self):
        truth = [
            {"id": "eval-control", "profile": "iid", "split": "evaluation",
             "hazard": False, "eligible_in_model": False,
             "truth": [{"observed": True, "true_ttc_s": None}]},
            {"id": "hazard", "profile": "iid", "split": "evaluation",
             "hazard": True, "eligible_in_model": True,
             "truth": [{"observed": True, "true_ttc_s": 1.0},
                       {"observed": True, "true_ttc_s": .7}]},
            {"id": "cal-control", "profile": "iid", "split": "calibration",
             "hazard": False, "eligible_in_model": False,
             "truth": [{"observed": True, "true_ttc_s": None}]},
        ]
        public = [{"id": "eval-control", "history": [{}]},
                  {"id": "hazard", "history": [{}, {}]},
                  {"id": "cal-control", "history": [{}]}]
        candidate = [
            {"id": "eval-control", "estimates": [{"point_ttc_s": 1.0,
                                                      "interval_s": [.8, 1.1]}]},
            {"id": "hazard", "estimates": [{"point_ttc_s": 1.0,
                                                "interval_s": [.9, 1.2]},
                                               {"point_ttc_s": .7,
                                                "interval_s": [.6, .8]}]},
            {"id": "cal-control", "estimates": [{"point_ttc_s": 2.5,
                                                    "interval_s": [2.4, 2.5]}]},
        ]
        truth_map = {x["id"]: x for x in truth}
        self.assertEqual(audit.threshold_for(candidate, truth_map, "point"), 2.0)
        late = [dict(x, estimates=[dict(e) for e in x["estimates"]]) for x in candidate]
        late[1]["estimates"][0]["interval_s"] = [2.6, 2.7]
        result = audit.score(public, truth, late)
        self.assertIn("hazard", result["decision_checks"]["paired_lead_failures"])
        self.assertEqual(result["profiles"]["iid"]["point_false_yield"], 1)


if __name__ == "__main__":
    unittest.main()
