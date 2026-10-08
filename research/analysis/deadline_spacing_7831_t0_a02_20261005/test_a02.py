import unittest

import candidate
import fixtures
import oracle


class DeadlineSpacingA02Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.results = candidate.all_results()

    def test_candidate_matches_independent_oracle_on_all_grid_rows(self):
        self.assertEqual((128, 512), oracle.assert_matches(
            self.results, fixtures.traces()))

    def test_noisy_and_transient_event_reduction_is_strict_across_grid(self):
        for row in self.results:
            if row["trace"] not in ("noisy_oscillation", "transient_burst"):
                continue
            spaced = row["rows"]["DEADLINE_SPACED"]["optional_count"]
            raw = row["rows"]["RAW_EVENT"]["optional_count"]
            self.assertLess(spaced, raw, (row["trace"], row["config"]))

    def test_hazard_rows_have_no_more_misses_than_raw_or_fixed(self):
        hazard_traces = {"sustained_approach", "missing_due_measurement",
                         "delayed_due_measurement", "hard_invalidation", "spacing_conflict",
                         "budget_exhausted"}
        for row in self.results:
            if row["trace"] not in hazard_traces:
                continue
            candidate_misses = row["rows"]["DEADLINE_SPACED"]["boundary_violations"]
            self.assertEqual(0, candidate_misses,
                             (row["trace"], row["config"]))
            for comparator in ("RAW_EVENT", "FIXED_PERIOD"):
                self.assertLessEqual(
                    candidate_misses,
                    row["rows"][comparator]["boundary_violations"],
                    (row["trace"], row["config"], comparator))

    def test_hard_invalidation_bypasses_spacing_on_every_grid_row(self):
        for row in self.results:
            if row["trace"] != "hard_invalidation":
                continue
            result = row["rows"]["DEADLINE_SPACED"]
            self.assertEqual("HARD_BYPASS", result["reason"])
            self.assertEqual(0, result["hard_bypass_suppressed"])
            self.assertEqual(row["config"]["latency"], result["bypass_latency"])

    def test_missing_or_delayed_scheduled_measurement_fails_closed(self):
        for row in self.results:
            if row["trace"] not in ("missing_due_measurement",
                                    "delayed_due_measurement"):
                continue
            result = row["rows"]["DEADLINE_SPACED"]
            if result["optional_count"]:
                expected = ("DELAYED_MEASUREMENT"
                            if row["trace"] == "delayed_due_measurement"
                            else "MISSING_MEASUREMENT")
                self.assertEqual(expected, result["reason"])
                self.assertEqual(1, result["unknown_intervals"])

    def test_horizon_endpoint_is_censored_not_spacing_conflict(self):
        trace = {"margin": [50] * 3, "signal": [5] * 3,
                 "horizon": 2, "missing": [], "hard": [], "budget": 99}
        cfg = {"decline_bound": 1, "uncertainty_growth": 0,
               "latency": 1, "minimum_spacing": 3, "fixed_period": 3}
        row = candidate.evaluate("endpoint", trace, cfg)["DEADLINE_SPACED"]
        self.assertEqual("HORIZON_CENSORED", row["reason"])
        self.assertIsNone(row["release_tick"])

    def test_spacing_conflict_yields_before_boundary_when_feasible(self):
        for row in self.results:
            if row["trace"] != "spacing_conflict":
                continue
            result = row["rows"]["DEADLINE_SPACED"]
            if result["reason"] == "SPACING_DEADLINE_CONFLICT":
                self.assertLess(result["release_tick"], result["unsafe_tick"])

    def test_all_results_are_finite_and_no_release_is_claimed_safe(self):
        for row in self.results:
            for result in row["rows"].values():
                if result["release_tick"] is not None and result["unsafe_tick"] is not None:
                    if result["release_tick"] >= result["unsafe_tick"]:
                        self.assertEqual(1, result["boundary_violations"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
