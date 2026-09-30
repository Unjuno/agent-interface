import unittest

import audit
import experiment


class ConstructionTests(unittest.TestCase):
    def test_fresh_construction_data_and_seed_separation(self):
        seeds = experiment.CONSTRUCTION_SEEDS
        self.assertTrue(set(seeds).isdisjoint(experiment.FORMAL_SEEDS.values()))
        first = experiment.run_experiment(seeds, per_block=20)
        second = experiment.run_experiment(seeds, per_block=20)
        self.assertEqual(experiment.canonical_bytes(first), experiment.canonical_bytes(second))
        self.assertEqual(first["seeds"], dict(zip(("train", "calibration", "test"), seeds)))
        self.assertEqual(first["train"]["mode_counts"], [400] * 5)
        self.assertEqual(len(first["calibration"]["rows"]), 100)
        self.assertEqual(len(first["test"]["rows"]), 100)
        for block in experiment.BLOCKS:
            rows = [r for r in first["test"]["rows"] if r["block"] == block]
            self.assertEqual(len(rows), 20)
            self.assertEqual([sum(r["mode"] == mode for r in rows) for mode in range(5)], [4] * 5)

    def test_threshold_is_calibration_only_and_matches_reference(self):
        result = experiment.run_experiment(experiment.CONSTRUCTION_SEEDS, per_block=20)
        summary = result["calibration"]["summary"]
        self.assertAlmostEqual(summary["direct_coverage"],
                               sum(r["direct_confidence"] >= summary["direct_threshold"]
                                   for r in result["calibration"]["rows"]) / 100)
        self.assertAlmostEqual(summary["typed_coverage"],
                               sum(r["typed_confidence"] >= summary["typed_threshold"]
                                   for r in result["calibration"]["rows"]) / 100)
        self.assertEqual(result, audit.reconstruct(dict(zip(("train", "calibration", "test"),
                                                             experiment.CONSTRUCTION_SEEDS)), 20))

    def test_independent_raw_comparator_rejects_all_corruptions(self):
        reference = audit.reconstruct(dict(zip(("train", "calibration", "test"),
                                                experiment.CONSTRUCTION_SEEDS)), 20)
        self.assertEqual(len(audit.mutations(reference)), 16)
        self.assertTrue(all(audit.changed_copy(reference, change) != reference
                            for change in audit.mutations(reference)))


if __name__ == "__main__":
    unittest.main()
