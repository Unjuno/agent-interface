"""Construction tests for the censored opportunity-tail candidate."""

import importlib.util
import hashlib
import json
from pathlib import Path
import tempfile
import unittest


MODULE_PATH = Path(__file__).with_name("candidate.py")


def load_candidate():
    if not MODULE_PATH.is_file():
        return None
    spec = importlib.util.spec_from_file_location("candidate_under_test", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class CandidateEstimatorTests(unittest.TestCase):
    def test_expected_shortfall_uses_fractional_mass_at_tail_boundary(self):
        candidate = load_candidate()
        self.assertIsNotNone(candidate, "candidate estimator is not implemented yet")
        # Tail mass is 1.25 of total weight 5: 10 contributes 1, 6 contributes .25.
        self.assertAlmostEqual(
            candidate.weighted_cvar([(10.0, 1.0), (6.0, 1.0), (2.0, 3.0)], 0.75),
            9.2,
        )

    def test_overlapping_route_bounds_return_unknown(self):
        candidate = load_candidate()
        self.assertIsNotNone(candidate, "candidate estimator is not implemented yet")
        self.assertEqual(
            candidate.rank_interval(2.5, 4.0, 3.0, 3.5)["state"],
            "UNKNOWN_OVERLAPPING_BOUNDS",
        )

    def test_point_rank_treats_floating_point_near_tie_as_tie(self):
        candidate = load_candidate()
        self.assertIsNotNone(candidate, "candidate estimator is not implemented yet")
        self.assertEqual(candidate._point_rank(1.0, 1.0 + 2e-16, "test") ["state"], "TIE")

    def test_near_zero_followup_positivity_withholds_point_estimate(self):
        candidate = load_candidate()
        self.assertIsNotNone(candidate, "candidate estimator is not implemented yet")
        result = candidate.ipcw_cvar(
            [
                {"resolved": True, "terminal_loss": 2.0, "p_resolve_model": 0.9},
                {"resolved": False, "p_resolve_model": 0.02},
            ],
            alpha=0.75,
            minimum_propensity=0.05,
        )
        self.assertEqual(result["status"], "UNSUPPORTED_POSITIVITY")
        self.assertIsNone(result["cvar"])

    def test_cohort_analysis_keeps_exact_stratum_tail_and_bounds(self):
        candidate = load_candidate()
        self.assertIsNotNone(candidate, "candidate estimator is not implemented yet")
        analyze = getattr(candidate, "analyze_cohort", None)
        self.assertIsNotNone(analyze, "candidate cohort analysis is not implemented yet")
        cohort = {
            "seed": 1,
            "arm": "no_censor",
            "opportunities": [
                {"opportunity_id": "a1", "route": "A", "stratum": "s0", "resolved": True, "followup_ticks": 4, "observed_increments": [3, 3, 3, 1], "terminal_loss": 10, "p_resolve_model": 1.0},
                {"opportunity_id": "a2", "route": "A", "stratum": "s0", "resolved": True, "followup_ticks": 4, "observed_increments": [0, 0, 0, 0], "terminal_loss": 0, "p_resolve_model": 1.0},
                {"opportunity_id": "b1", "route": "B", "stratum": "s0", "resolved": True, "followup_ticks": 4, "observed_increments": [3, 1, 0, 0], "terminal_loss": 4, "p_resolve_model": 1.0},
                {"opportunity_id": "b2", "route": "B", "stratum": "s0", "resolved": True, "followup_ticks": 4, "observed_increments": [3, 1, 0, 0], "terminal_loss": 4, "p_resolve_model": 1.0},
            ],
        }
        actual = analyze(cohort, alpha=0.5, minimum_propensity=0.05, horizon=4, max_per_tick=3)
        self.assertEqual(actual["routes"]["A"]["macro_cvar_resolved_only"], 10.0)
        self.assertEqual(actual["routes"]["B"]["macro_cvar_resolved_only"], 4.0)
        self.assertEqual(actual["ranking"]["partial_tail"]["state"], "A_WORSE_IDENTIFIED")

    def test_invalid_positivity_threshold_is_rejected(self):
        candidate = load_candidate()
        self.assertIsNotNone(candidate, "candidate estimator is not implemented yet")
        with self.assertRaises(ValueError):
            candidate.ipcw_cvar(
                [{"resolved": True, "terminal_loss": 2.0, "p_resolve_model": 0.9}],
                alpha=0.75,
                minimum_propensity=-0.1,
            )

    def test_cli_binds_raw_output_to_exact_public_input_bytes_and_refuses_overwrite(self):
        candidate = load_candidate()
        self.assertIsNotNone(candidate, "candidate estimator is not implemented yet")
        public = {
            "schema": "8598-observed-v1",
            "settings": {"horizon": 1, "max_regret_per_tick": 1, "cvar_alpha": 0.5, "minimum_completion_propensity": 0.05},
            "cohorts": [{"seed": 0, "arm": "no_censoring", "opportunities": [
                {"opportunity_id": "a", "route": "A", "stratum": "s0", "resolved": True, "followup_ticks": 1, "observed_increments": [1], "terminal_loss": 1, "p_resolve_model": 1.0},
                {"opportunity_id": "b", "route": "B", "stratum": "s0", "resolved": True, "followup_ticks": 1, "observed_increments": [0], "terminal_loss": 0, "p_resolve_model": 1.0},
            ]}],
            "categorical_controls": [],
        }
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            input_path = root / "public.json"
            output_path = root / "candidate.json"
            source = json.dumps(public, sort_keys=True, separators=(",", ":")).encode("utf-8") + b"\n"
            input_path.write_bytes(source)
            candidate.main(["--input", str(input_path), "--output", str(output_path)])
            raw = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertEqual(raw["input_sha256"], hashlib.sha256(source).hexdigest())
            with self.assertRaises(FileExistsError):
                candidate.main(["--input", str(input_path), "--output", str(output_path)])


if __name__ == "__main__":
    unittest.main()
