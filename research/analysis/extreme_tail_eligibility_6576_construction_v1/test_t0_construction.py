import unittest

from research.analysis.extreme_tail_eligibility_6576_construction_v1.t0_audit import (
    _expected_decision,
    _oracle_cp95,
    _oracle_rows,
)
from research.analysis.extreme_tail_eligibility_6576_construction_v1.t0_candidate import (
    _clopper_pearson,
    _score_prediction,
    generate,
)


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


if __name__ == "__main__":
    unittest.main()
