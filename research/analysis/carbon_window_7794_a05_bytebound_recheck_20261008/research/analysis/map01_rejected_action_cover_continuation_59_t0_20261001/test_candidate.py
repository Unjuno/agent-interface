"""Tests for a bounded, no-authority continuation-admission experiment.

Mutations these tests must catch:
- using the rejected primary action's tighter loss cap for the cover;
- accepting a cover one health point below its derived floor;
- accepting missing, stale, or wrong-source evidence;
- allowing cover admission to imply any primary-action/input authority.
"""
import unittest

from candidate import evaluate


class ContinuationAdmissionTests(unittest.TestCase):
    def test_retained_boundary_rejects_action_but_separately_admits_cover(self):
        result = evaluate(
            source_health=97, current_health=85,
            action_max_loss=8, cover_max_loss=12,
            cover_critical_minimum=25, evidence_age_ms=0,
            max_evidence_age_ms=30000, source_matches=True)
        self.assertEqual(result["action"], "REJECT")
        self.assertEqual(result["cover"], "ADMIT_BOUNDED_CONTINUATION")
        self.assertFalse(result["input_authority"])

    def test_health_below_cover_floor_rejects(self):
        result = evaluate(97, 84, 8, 12, 25, 0, 30000, True)
        self.assertEqual(result["cover"], "REJECT")
        self.assertFalse(result["input_authority"])

    def test_health_above_cover_floor_can_admit_without_action_authority(self):
        result = evaluate(97, 86, 8, 12, 25, 0, 30000, True)
        self.assertEqual(result["cover"], "ADMIT_BOUNDED_CONTINUATION")
        self.assertEqual(result["action"], "REJECT")
        self.assertFalse(result["input_authority"])

    def test_missing_health_fails_closed(self):
        result = evaluate(97, None, 8, 12, 25, 0, 30000, True)
        self.assertEqual(result["cover"], "REJECT")

    def test_stale_evidence_fails_closed_at_age_boundary_plus_one(self):
        result = evaluate(97, 85, 8, 12, 25, 30001, 30000, True)
        self.assertEqual(result["cover"], "REJECT")

    def test_mismatched_source_fails_closed(self):
        result = evaluate(97, 85, 8, 12, 25, 0, 30000, False)
        self.assertEqual(result["cover"], "REJECT")


if __name__ == "__main__":
    unittest.main()
