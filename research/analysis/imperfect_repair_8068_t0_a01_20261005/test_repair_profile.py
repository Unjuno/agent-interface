import unittest

from repair_profile import enumerate_histories, summarize


class RepairProfileTests(unittest.TestCase):
    def test_distinguishes_three_repair_operators(self):
        rows = enumerate_histories()
        profiles = summarize(rows)
        self.assertEqual(profiles["perfect"]["recurrence_count"], 0)
        self.assertGreater(profiles["minimal"]["recurrence_count"], 0)
        self.assertGreater(profiles["minimal"]["recurrence_count"], profiles["partial"]["recurrence_count"])

    def test_equal_exposure_is_required_for_comparison(self):
        rows = enumerate_histories()
        with self.assertRaises(ValueError):
            summarize(rows[:-1])

    def test_censoring_is_not_counted_as_nonrecurrence(self):
        rows = enumerate_histories()
        profile = summarize(rows)
        self.assertEqual(profile["perfect"]["censored_count"], 4)

    def test_history_specific_partial_repair_retains_latent_state(self):
        rows = enumerate_histories()
        partial = [row for row in rows if row["operator"] == "partial"]
        self.assertTrue(any(row["pre_repair_state"] != row["post_repair_state"] for row in partial))
        self.assertTrue(all(row["post_repair_state"] >= 0 for row in partial))


if __name__ == "__main__":
    unittest.main()
