import unittest

from experiment import alias_counts, corpus, features, rms_noise


class ConstructionTests(unittest.TestCase):
    def test_required_families_are_present(self):
        names = {r["family"] for r in corpus()}
        self.assertTrue({
            "monotonic_useful_convergence", "monotonic_divergence",
            "high_decelerating_reversal", "low_confidence_accelerating_correct",
            "plateau", "overshoot", "oscillation", "transient_spike",
            "stale_previous_sample", "epoch_change", "missing_sample",
            "irregular_sample_intervals", "self_correcting_state",
            "uncertain_state", "action_required_state",
        }.issubset(names))

    def test_level_only_aliases_have_different_labels(self):
        self.assertEqual(alias_counts(corpus())["current_level_alias_groups"], 4)

    def test_velocity_aliases_require_acceleration(self):
        a = alias_counts(corpus())
        self.assertEqual(a["same_level_velocity_different_label_pairs"], 4)
        self.assertEqual(a["acceleration_separates_second_order_pairs"], 4)

    def test_invalid_history_yields(self):
        bad = [r for r in corpus() if r["validity"] != "valid"]
        self.assertEqual(len(bad), 3)
        self.assertTrue(all(r["label"] == "YIELD" and features(r) is None for r in bad))

    def test_noop_and_yield_are_distinct(self):
        labels = {r["label"] for r in corpus()}
        self.assertIn("NO_OP", labels)
        self.assertIn("YIELD", labels)
        self.assertNotEqual("NO_OP", "YIELD")

    def test_curvature_noise_exceeds_velocity_and_smoothing_reduces_it(self):
        n = rms_noise()
        self.assertEqual(n["triples"], 27)
        self.assertGreater(n["raw_acceleration_rms"], n["velocity_rms"])
        self.assertLess(n["causally_smoothed_acceleration_rms"], n["raw_acceleration_rms"])


if __name__ == "__main__":
    unittest.main()
