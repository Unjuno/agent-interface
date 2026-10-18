from __future__ import annotations

import json
import unittest
from pathlib import Path

from candidate import run_experiment

HERE = Path(__file__).resolve().parent


class RetainedScreenshotGroundingTests(unittest.TestCase):
    def test_replays_frozen_observed_outcome_matrix(self):
        result = run_experiment()
        actual = [(row["task"], row["role"], row["status"], row["eligible"])
                  for row in result["cases"]]
        expected = [
            (2, "field", "VALID", True), (2, "submit", "VALID", True),
            (3, "field", "VALID", True), (3, "submit", "VALID", True),
            (4, "field", "FLAT_REFUSED", False), (4, "submit", "VALID", True),
            (5, "field", "FLAT_REFUSED", False), (5, "submit", "VALID", True),
            (6, "field", "FLAT_REFUSED", False), (6, "submit", "VALID", True),
        ]
        self.assertEqual(actual, expected)
        self.assertEqual(result["summary"], {
            "coordinate_count": 10, "valid": 7, "flat_refused": 3,
            "other_status": 0, "input_dispatch_count": 0,
            "model_call_count": 0, "gui_call_count": 0,
        })

    def test_flat_refusal_does_not_mint_registry_entry(self):
        result = run_experiment()
        refusals = [row for row in result["cases"] if row["status"] == "FLAT_REFUSED"]
        self.assertEqual([row["task"] for row in refusals], [4, 5, 6])
        self.assertTrue(all(row["role"] == "field" and row["registry_entries"] == 0
                            for row in refusals))


if __name__ == "__main__":
    unittest.main(verbosity=2)
