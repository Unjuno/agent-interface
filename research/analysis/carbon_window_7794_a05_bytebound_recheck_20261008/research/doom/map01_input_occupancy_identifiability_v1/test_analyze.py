"""Construction controls for held-input telemetry identifiability."""

import unittest

from analyze import summarize


class IdentifiabilityTests(unittest.TestCase):
    def test_program_level_empty_release_is_not_per_key_release(self):
        rows = [
            {"event": "input_admission", "key": "Up", "input_ack_ns": 100},
            {"event": "keys_held", "keys": ["Up"], "input_ack_ns": 110},
            {
                "event": "terminal",
                "release": {
                    "verified": True,
                    "keys_down": [],
                    "buttons_down": [],
                    "verified_ns": 200,
                },
            },
        ]
        result = summarize(rows)
        self.assertEqual(result["verified_empty_terminal_count"], 1)
        self.assertEqual(result["explicit_per_key_release_count"], 0)
        self.assertFalse(result["physical_occupancy_identifiable"])

    def test_positive_control_recognizes_typed_per_key_release(self):
        rows = [
            {
                "event": "key_released",
                "key": "Up",
                "release_ns": 200,
            }
        ]
        result = summarize(rows)
        self.assertEqual(result["explicit_per_key_release_count"], 1)
        self.assertTrue(result["physical_occupancy_identifiable"])

    def test_release_without_key_identity_is_not_per_key_evidence(self):
        rows = [{"event": "key_released", "release_ns": 200}]
        result = summarize(rows)
        self.assertEqual(result["explicit_per_key_release_count"], 0)
        self.assertFalse(result["physical_occupancy_identifiable"])

    def test_key_identity_without_timestamp_is_not_per_key_evidence(self):
        rows = [{"event": "key_released", "key": "Up"}]
        result = summarize(rows)
        self.assertEqual(result["explicit_per_key_release_count"], 0)
        self.assertFalse(result["physical_occupancy_identifiable"])


if __name__ == "__main__":
    unittest.main()
