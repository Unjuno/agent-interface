import unittest

from ledger import summarize


def valid_rows():
    return [
        {
            "kind": "key_interval", "action_id": "act-1", "epoch": 7,
            "key": "W", "press_request_ns": 100, "press_sync_ns": 110,
            "down_sample_ns": 111, "release_request_ns": 130,
            "release_sync_ns": 140, "up_sample_ns": 141,
            "source": "input-owner-v11",
        },
        {
            "kind": "verified_empty", "action_id": "act-1", "epoch": 7,
            "timestamp_ns": 200, "keys_down": [], "source": "xquerykeymap",
        },
    ]


class OccupancyLedgerTests(unittest.TestCase):
    def test_reports_only_a_bracketed_per_key_occupancy_interval(self):
        result = summarize(valid_rows())
        self.assertEqual(result["status"], "BOUNDED")
        self.assertEqual(result["intervals"], [{"action_id": "act-1", "epoch": 7,
                                                 "key": "W", "lower_ns": 20,
                                                 "upper_ns": 40}])

    def test_missing_key_up_receipt_is_unknown_not_program_envelope(self):
        rows = valid_rows()
        rows[0].pop("release_sync_ns")
        result = summarize(rows)
        self.assertEqual(result["status"], "UNKNOWN")
        self.assertIn("missing_or_invalid_key_bracket", result["reasons"])

    def test_empty_snapshot_must_bind_same_action_epoch_and_keys(self):
        rows = valid_rows()
        rows[1]["action_id"] = "other-action"
        result = summarize(rows)
        self.assertEqual(result["status"], "UNKNOWN")
        self.assertIn("empty_receipt_identity_mismatch", result["reasons"])

    def test_reversed_or_boolean_timestamps_fail_closed(self):
        rows = valid_rows()
        rows[0]["release_request_ns"] = True
        result = summarize(rows)
        self.assertEqual(result["status"], "UNKNOWN")
        self.assertIn("invalid_timestamp_order_or_type", result["reasons"])

    def test_two_overlapping_keys_keep_separate_bounds(self):
        rows = valid_rows()
        rows[0].update({"release_request_ns": 180, "release_sync_ns": 190,
                        "up_sample_ns": 191})
        rows.insert(1, {
            "kind": "key_interval", "action_id": "act-1", "epoch": 7,
            "key": "SPACE", "press_request_ns": 120, "press_sync_ns": 128,
            "down_sample_ns": 129, "release_request_ns": 160,
            "release_sync_ns": 170, "up_sample_ns": 171,
            "source": "input-owner-v11",
        })
        result = summarize(rows)
        self.assertEqual(result["status"], "BOUNDED")
        self.assertEqual(result["intervals"], [
            {"action_id": "act-1", "epoch": 7, "key": "SPACE", "lower_ns": 32, "upper_ns": 50},
            {"action_id": "act-1", "epoch": 7, "key": "W", "lower_ns": 70, "upper_ns": 90},
        ])

    def test_non_object_or_unrecognized_event_cannot_be_ignored(self):
        rows = valid_rows() + ["garbage"]
        result = summarize(rows)
        self.assertEqual(result["status"], "UNKNOWN")
        self.assertIn("unknown_or_malformed_row", result["reasons"])


if __name__ == "__main__":
    unittest.main()
