from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from posthoc_audit import event_time_effect_present, timing_disposition


class PosthocAuditTests(unittest.TestCase):
    def test_late_effect_is_descriptive_miss_and_unbounded_snapshot_holds(self):
        payload = {"trial_id": "t1", "value": "ok"}
        self.assertTrue(event_time_effect_present(payload, payload, 99, 100))
        self.assertFalse(event_time_effect_present(payload, payload, 101, 100))
        self.assertFalse(event_time_effect_present({"trial_id": "other"}, payload, 99, 100))
        self.assertEqual(timing_disposition([0], []), "EXACT_DEADLINE_SAMPLES")
        self.assertEqual(timing_disposition([1], []), "HOLD_AUDIT_TIMING")
        self.assertEqual(timing_disposition([0], ["corruption"]), "STOP_REVIEW_ERRORS")


if __name__ == "__main__":
    unittest.main()
