import unittest

from .probe import MODEL_POINT, REGION, image_with_target, mint_model_coordinate, new_store, observation, run_probe


class CoordinateGroundingTests(unittest.TestCase):
    def test_new_coordinate_mints_reference_and_fresh_exact_pixels_resolve(self):
        source = image_with_target()
        store = new_store()
        minted = mint_model_coordinate(store, list(MODEL_POINT), observation(1, 1_000_000), source)
        result = store.resolve_point(
            minted["handle"], [REGION // 2, REGION // 2], observation(2, 2_000_000),
            source.copy(), 3_000_000,
        )
        self.assertEqual(result["status"], "VALID")
        self.assertEqual(result["point"], MODEL_POINT)
        self.assertIn("ordinary admission remains required", result["authority"])

    def test_changed_pixels_fail_closed(self):
        self.assertEqual(run_probe()["case_results"]["changed_target"]["status"], "MISSING")
        self.assertFalse(run_probe()["case_results"]["changed_target"]["eligible"])

    def test_duplicate_exact_regions_are_ambiguous(self):
        self.assertEqual(run_probe()["case_results"]["duplicate_target"]["status"], "AMBIGUOUS")

    def test_focus_change_is_out_of_scope(self):
        self.assertEqual(run_probe()["case_results"]["focus_changed"]["status"], "SCOPE_MISMATCH")

    def test_window_translation_revalidates_same_target(self):
        result = run_probe()["case_results"]["window_translation"]
        self.assertEqual(result["status"], "REVALIDATED")
        self.assertEqual(result["point"], [MODEL_POINT[0] + 5, MODEL_POINT[1]])

    def test_local_movement_is_not_silently_admitted(self):
        self.assertEqual(run_probe()["case_results"]["local_move"]["status"], "MOVED")

    def test_stale_observation_and_missing_alias_refuse(self):
        results = run_probe()["case_results"]
        self.assertEqual(results["stale_observation"]["status"], "STALE")
        self.assertEqual(results["missing_alias"]["status"], "MISSING")

    def test_flat_source_and_out_of_bounds_coordinate_refuse_before_authority(self):
        result = run_probe()
        self.assertTrue(result["flat_source_refused_before_registry_insert"])
        self.assertTrue(result["out_of_bounds_refused"])
        self.assertEqual(result["input_dispatch_count"], 0)


if __name__ == "__main__":
    unittest.main()
