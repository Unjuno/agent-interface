from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from candidate import build_raw
from audit import audit, reconstruct, validate


ROOT = Path(__file__).parent


class NotificationSamplingMethodTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = json.loads((ROOT / "fixture.json").read_text(encoding="utf-8"))
        cls.raw = build_raw(cls.fixture)
        cls.expected = reconstruct(cls.fixture)

    def test_exact_clock_truth_equals_uniform_random_epoch_expectation(self):
        self.assertEqual(48, self.raw["clock_time"]["no_progress_ticks"])
        self.assertEqual(0.8, self.raw["clock_time"]["no_progress_fraction"])
        self.assertEqual(self.raw["clock_time"]["no_progress_fraction"],
                         self.raw["exogenous_random_epochs"]["exact_uniform_epoch_no_progress_fraction"])

    def test_seeded_epoch_sample_is_separate_from_exact_expectation(self):
        rows = self.raw["exogenous_random_epochs"]
        self.assertEqual(12, rows["draw_count"])
        self.assertEqual(12, len(rows["draw_ticks"]))
        self.assertFalse(rows["schedule_visible_to_notification_policy"])
        self.assertNotEqual(rows["sample_no_progress_fraction"], rows["exact_uniform_epoch_no_progress_fraction"])

    def test_notifications_change_only_reactive_schedule_in_fixture(self):
        arms = self.raw["arms"]
        self.assertEqual(arms["silent"]["check_ins"], arms["milestone_visible_nonreactive_control"]["check_ins"])
        self.assertNotEqual(arms["silent"]["check_ins"], arms["milestone_reactive"]["check_ins"])
        self.assertNotEqual(arms["silent"]["check_ins"], arms["noisy_status_reactive"]["check_ins"])

    def test_progress_gaps_retain_long_and_short_intervals(self):
        durations = [row["duration_ticks"] for row in self.raw["progress_gaps"]]
        self.assertEqual([4, 26, 3, 27], durations)
        self.assertEqual(60, sum(durations))
        self.assertEqual(60, len(self.raw["no_progress_by_tick"]))

    def test_independent_interval_reconstruction_matches_candidate(self):
        self.assertTrue(validate(self.fixture, self.raw))
        self.assertEqual(self.raw, self.expected)

    def test_auditor_rejects_epoch_leak_and_dropped_long_gap(self):
        result = audit(self.fixture, self.raw)
        self.assertEqual("PASS_METHOD_SCOPED", result["status"])
        self.assertTrue(all(result["mutation_controls"].values()))
        corrupt = copy.deepcopy(self.raw)
        corrupt["progress_gaps"].pop(1)
        self.assertFalse(validate(self.fixture, corrupt))


if __name__ == "__main__":
    unittest.main()
