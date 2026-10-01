import unittest

from candidate import execute_trace


class ReorderedResponseTests(unittest.TestCase):
    def test_request_does_not_itself_restore_freshness(self):
        r = execute_trace(["INVALIDATE", "POLL", "ACT"])
        self.assertEqual(len(r["requests"]), 1)
        self.assertFalse(r["actions"][0]["admitted"])

    def test_polls_do_not_duplicate_request(self):
        r = execute_trace(["INVALIDATE", "POLL", "POLL", "POLL", "POLL"])
        self.assertEqual(len(r["requests"]), 1)

    def test_current_linked_response_allows_action(self):
        r = execute_trace(["INVALIDATE", "POLL", "OBS_MATCH", "ACT"])
        self.assertTrue(r["observations"][0]["linked"])
        self.assertTrue(r["actions"][0]["admitted"])

    def test_old_response_after_supersession_stays_stale(self):
        r = execute_trace(["INVALIDATE", "POLL", "INVALIDATE", "POLL", "OBS_OLD_REQUEST", "ACT"])
        self.assertEqual([x["generation"] for x in r["requests"]], [1, 2])
        self.assertFalse(r["observations"][0]["linked"])
        self.assertFalse(r["actions"][0]["admitted"])

    def test_new_response_after_old_response_restores_latest_generation(self):
        r = execute_trace(["INVALIDATE", "POLL", "INVALIDATE", "POLL",
                           "OBS_OLD_REQUEST", "OBS_MATCH", "ACT"])
        self.assertFalse(r["observations"][0]["linked"])
        self.assertTrue(r["observations"][1]["linked"])
        self.assertTrue(r["actions"][0]["admitted"])

    def test_unlinked_response_stays_stale(self):
        r = execute_trace(["INVALIDATE", "POLL", "OBS_UNLINKED", "ACT"])
        self.assertFalse(r["actions"][0]["admitted"])

    def test_replayed_sequence_stays_stale(self):
        r = execute_trace(["INVALIDATE", "POLL", "OBS_REPLAY", "ACT"])
        self.assertFalse(r["actions"][0]["admitted"])

    def test_initial_fresh_observation_allows_action(self):
        self.assertTrue(execute_trace(["ACT"])["actions"][0]["admitted"])


if __name__ == "__main__":
    unittest.main()
