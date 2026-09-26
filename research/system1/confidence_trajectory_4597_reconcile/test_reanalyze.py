import json
import tempfile
import unittest
from pathlib import Path

from reanalyze import expected


class FrozenRuleTests(unittest.TestCase):
    def test_falling_high_confidence_retains_current_only_positive(self):
        case = {"current_valid": True, "state": "ACTION_REQUIRED", "history_status": "VALID", "scores": [0.94, 0.87, 0.77], "times_ms": [0, 100, 200]}
        self.assertEqual(expected(case, "CURRENT_ONLY"), "ACTION")
        self.assertEqual(expected(case, "LEVEL_PLUS_VELOCITY"), "ACTION")

    def test_low_confidence_rising_rescue(self):
        case = {"current_valid": True, "state": "ACTION_REQUIRED", "history_status": "VALID", "scores": [0.14, 0.32, 0.60], "times_ms": [0, 100, 200]}
        self.assertEqual(expected(case, "LEVEL_PLUS_VELOCITY"), "ACTION")

    def test_invalid_history_falls_back(self):
        case = {"current_valid": True, "state": "ACTION_REQUIRED", "history_status": "STALE_PREVIOUS", "scores": [0.55, 0.72, 0.95], "times_ms": [0, 100, 200]}
        self.assertEqual(expected(case, "LEVEL_PLUS_VELOCITY"), "ACTION")


if __name__ == "__main__":
    unittest.main()
