import unittest

from recheck_review import compare_streams


class ReviewRecheckTests(unittest.TestCase):
    def test_split_streams_must_match_observed_raw_projection(self):
        raw = [{"event": "heartbeat", "sequence": 0}]
        observed = [{"event": "heartbeat", "sequence": 0,
                     "observer_received_monotonic_ns": 101}]
        heartbeat = [{**raw[0], "observer_received_monotonic_ns": 101}]
        self.assertEqual([], compare_streams(raw, observed, heartbeat, []))
        self.assertIn(
            "heartbeat split differs from projected observed raw stream",
            compare_streams(raw, observed, [{**heartbeat[0], "sequence": 9}], []),
        )

    def test_stream_count_mismatch_fails(self):
        self.assertIn(
            "raw and observer event counts differ",
            compare_streams([{"event": "heartbeat"}], [], [], []),
        )


if __name__ == "__main__":
    unittest.main()
