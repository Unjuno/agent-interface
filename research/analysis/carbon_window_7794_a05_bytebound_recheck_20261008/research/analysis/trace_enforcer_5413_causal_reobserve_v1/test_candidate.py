import unittest

from candidate import execute_trace


class CausalReobserveTests(unittest.TestCase):
    def test_request_is_not_observation(self):
        row = execute_trace(["INVALIDATE", "POLL", "ACT"])
        self.assertEqual(len(row["requests"]), 1)
        self.assertFalse(row["actions"][0]["admitted"])
        self.assertTrue(row["final"]["stale"])

    def test_repeated_poll_does_not_duplicate_pending_request(self):
        row = execute_trace(["INVALIDATE", "POLL", "POLL", "POLL"])
        self.assertEqual(len(row["requests"]), 1)

    def test_matching_new_observation_clears_current_generation(self):
        row = execute_trace(["INVALIDATE", "POLL", "OBS_MATCH", "ACT"])
        self.assertTrue(row["observations"][0]["linked"])
        self.assertTrue(row["actions"][0]["admitted"])

    def test_unlinked_observation_does_not_clear(self):
        row = execute_trace(["INVALIDATE", "POLL", "OBS_UNLINKED", "ACT"])
        self.assertFalse(row["observations"][0]["linked"])
        self.assertFalse(row["actions"][0]["admitted"])

    def test_replayed_sequence_does_not_clear(self):
        row = execute_trace(["INVALIDATE", "POLL", "OBS_REPLAY", "ACT"])
        self.assertFalse(row["observations"][0]["linked"])
        self.assertFalse(row["actions"][0]["admitted"])

    def test_superseded_request_does_not_clear_new_invalidation(self):
        row = execute_trace(["INVALIDATE", "POLL", "INVALIDATE", "OBS_OLD_REQUEST", "ACT"])
        self.assertFalse(row["observations"][0]["linked"])
        self.assertFalse(row["actions"][0]["admitted"])

    def test_second_invalidation_requires_new_current_request(self):
        row = execute_trace(["INVALIDATE", "POLL", "OBS_MATCH", "INVALIDATE", "POLL", "OBS_MATCH", "ACT"])
        self.assertEqual([x["generation"] for x in row["requests"]], [1, 2])
        self.assertTrue(row["actions"][0]["admitted"])

    def test_initial_fresh_observation_allows_action(self):
        row = execute_trace(["ACT"])
        self.assertTrue(row["actions"][0]["admitted"])


if __name__ == "__main__":
    unittest.main()
