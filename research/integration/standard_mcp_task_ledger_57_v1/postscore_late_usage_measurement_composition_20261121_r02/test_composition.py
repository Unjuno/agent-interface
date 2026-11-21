"""Verify usage-complete and missing-usage composition controls."""

import tempfile
import unittest
from pathlib import Path

from composition import run_case


class LateUsageMeasurementCompositionTests(unittest.TestCase):
    def test_post_score_late_usage_reaches_measured_run_totals(self):
        with tempfile.TemporaryDirectory() as temporary:
            result = run_case(Path(temporary) / "positive",
                              late_usage_available=True)
        self.assertTrue(result["late_usage_observed"])
        self.assertEqual(result["late_usage_observation_count"], 1)
        self.assertEqual(result["usage_status"], "complete")
        self.assertEqual(result["input_tokens"], 18)
        self.assertEqual(result["output_tokens"], 3)
        self.assertIsNone(result["task_success"])
        self.assertEqual(result["independent_score_status"], "recorded")
        self.assertEqual(result["relay_calls"], 0)

    def test_missing_usage_keeps_comparison_totals_unknown(self):
        with tempfile.TemporaryDirectory() as temporary:
            result = run_case(Path(temporary) / "negative",
                              late_usage_available=False)
        self.assertFalse(result["late_usage_observed"])
        self.assertEqual(result["usage_status"], "incomplete")
        self.assertIsNone(result["input_tokens"])
        self.assertIsNone(result["output_tokens"])
        self.assertIsNone(result["task_success"])
        self.assertEqual(result["relay_calls"], 0)


if __name__ == "__main__":
    unittest.main()
