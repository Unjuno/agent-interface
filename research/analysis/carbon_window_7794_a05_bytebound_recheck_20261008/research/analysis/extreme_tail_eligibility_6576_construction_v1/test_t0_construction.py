import unittest
import json
import tempfile
from pathlib import Path

from research.analysis.extreme_tail_eligibility_6576_construction_v1.t0_audit import (
    _expected_decision,
    _oracle_cp95,
    _oracle_gpd_quantile,
    _oracle_rows,
    _oracle_tailid,
    audit,
)
from research.analysis.extreme_tail_eligibility_6576_construction_v1.t0_candidate import (
    _clopper_pearson,
    _gpd_quantile,
    _score_prediction,
    generate,
    run,
)
from research.analysis.extreme_tail_eligibility_6576_construction_v1.tailid_equivalent import tailid_sensitive_upper


class T0ConstructionTests(unittest.TestCase):
    def setUp(self):
        self.config = {
            "censor_limit": 3.5,
            "threshold_probability": 0.9,
            "minimum_tail_events_per_mode": 4,
            "max_block_median_ratio": 1.5,
            "max_lag1_tail_indicator_correlation": 0.1,
        }

    def test_candidate_generation_matches_separate_raw_oracle(self):
        for kind, modes in (
            ("exponential", ["normal"]), ("mixture", ["normal", "cleanup"]),
            ("drift", ["normal"]), ("cluster", ["normal"]),
            ("censored", ["normal"]), ("hidden_mode", ["normal", "cleanup"]),
        ):
            case = {"case_id": kind, "seed": 65761001, "kind": kind, "declared_modes": modes}
            for stream in ("train", "holdout"):
                with self.subTest(kind=kind, stream=stream):
                    self.assertEqual(generate(case, 200, stream, self.config), _oracle_rows(case, 200, stream, self.config))

    def test_hidden_declared_mode_is_not_estimable(self):
        case = {"case_id": "hidden", "seed": 65761006, "kind": "hidden_mode", "declared_modes": ["normal", "cleanup"]}
        rows = generate(case, 200, "train", self.config)
        self.assertEqual(_expected_decision(rows, case, self.config), "NOT_ESTIMABLE_MODE_COVERAGE")

    def test_censored_population_is_not_estimable(self):
        case = {"case_id": "censored", "seed": 65761005, "kind": "censored", "declared_modes": ["normal"]}
        rows = generate(case, 200, "train", self.config)
        self.assertGreater(sum(row["censored"] for row in rows), 0)
        self.assertEqual(_expected_decision(rows, case, self.config), "NOT_ESTIMABLE_CENSORED_ENDPOINT")

    def test_exact_binomial_interval_implementations_agree(self):
        for count in (0, 20, 40, 60, 400):
            with self.subTest(count=count):
                candidate = _clopper_pearson(count, 4000)
                oracle = _oracle_cp95(count, 4000)
                self.assertAlmostEqual(candidate[0], oracle[0], places=12)
                self.assertAlmostEqual(candidate[1], oracle[1], places=12)

    def test_censored_holdout_is_not_scored_as_uncensored_population(self):
        rows = [{"latent": 0.5, "censored": False}, {"latent": 9.0, "censored": True}]
        fit = {"status": "ESTIMATED", "p99": 1.0}
        score = _score_prediction(rows, fit, 0.01)
        self.assertIsNone(score["exceedances"])
        self.assertIsNone(score["cp95"])
        self.assertEqual(score["n_uncensored"], 1)
        self.assertEqual(score["reason"], "NOT_ESTIMABLE_CENSORED_HOLDOUT")

    def test_independent_profile_oracle_reconstructs_candidate_fit_and_tailid_selection(self):
        config = {
            "threshold_probability": 0.9,
            "tailid_confidence": 0.9999,
            "tailid_candidate_fraction": 0.05,
            "censor_limit": 3.5,
        }
        cases = (
            ("exponential", ["normal"]),
            ("mixture", ["normal", "cleanup"]),
            ("drift", ["normal"]),
            ("cluster", ["normal"]),
            ("censored", ["normal"]),
            ("hidden_mode", ["normal", "cleanup"]),
        )
        for seed, (kind, modes) in enumerate(cases, start=65769901):
            case = {"case_id": kind, "seed": seed, "kind": kind, "declared_modes": modes}
            rows = _oracle_rows(case, 400, "train", config)
            sample = [row["observed"] for row in rows]
            with self.subTest(kind=kind):
                candidate_fit = _gpd_quantile(sample, 0.9, 0.99)
                oracle_fit = _oracle_gpd_quantile(sample, 0.9, 0.99)
                self.assertEqual(candidate_fit["status"], oracle_fit["status"])
                for key in ("threshold", "scale", "shape", "p99"):
                    self.assertAlmostEqual(candidate_fit[key], oracle_fit[key], delta=2e-4)
                candidate_tailid = tailid_sensitive_upper(sample, threshold_probability=0.9, confidence=config["tailid_confidence"], candidate_fraction_of_tail=config["tailid_candidate_fraction"])
                oracle_tailid = _oracle_tailid(sample, config)
                self.assertEqual(candidate_tailid["candidate_count"], oracle_tailid["candidate_count"])
                self.assertEqual(candidate_tailid["sensitive"], oracle_tailid["sensitive"])

    def test_raw_auditor_accepts_toy_run_and_rejects_corrupted_p99(self):
        config = {
            "schema": "unjuno.agent-interface.issue-6576.t0-cases.v1",
            "n_train": 400,
            "n_holdout": 400,
            "nominal_exceedance_probability": 0.05,
            "threshold_probability": 0.8,
            "minimum_tail_events_per_mode": 4,
            "max_block_median_ratio": 100.0,
            "max_lag1_tail_indicator_correlation": 1.0,
            "censor_limit": 3.5,
            "tailid_candidate_fraction": 0.05,
            "tailid_confidence": 0.9999,
            "cases": [{"case_id": "stationary_light_tail", "seed": 65769999, "kind": "exponential", "declared_modes": ["normal"]}],
        }
        with tempfile.TemporaryDirectory() as directory:
            config_path = Path(directory) / "cases.json"
            result_path = Path(directory) / "result.json"
            config_path.write_text(json.dumps(config, sort_keys=True, separators=(",", ":")))
            result = run(config_path)
            result_path.write_text(json.dumps(result, sort_keys=True, separators=(",", ":")))
            passed, message = audit(config_path, result_path)
            self.assertTrue(passed, message)
            result["results"][0]["naive_evt"]["p99"] += 0.25
            result_path.write_text(json.dumps(result, sort_keys=True, separators=(",", ":")))
            passed, message = audit(config_path, result_path)
            self.assertFalse(passed)
            self.assertIn("FAIL_NAIVE_EVT_P99", message)


if __name__ == "__main__":
    unittest.main()
