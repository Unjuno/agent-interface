import unittest

from dependencies.serialize_release import join_explicit_release


class MergedSerializerIntegrationTests(unittest.TestCase):
    def test_merged_helper_joins_owner_and_caller_without_losing_provenance(self):
        owner = {"event": "owner_key_release_bracket", "key": "a", "request_started_ns": 10}
        caller = {"case": "single_explicit", "caller_started_ns": 5, "caller_returned_ns": 20}
        result = join_explicit_release(owner, caller)
        self.assertEqual(result["event"], "joined_release")
        self.assertEqual(result["owner_event"], "owner_key_release_bracket")
        self.assertEqual(result["key"], "a")
        self.assertEqual(result["case"], "single_explicit")
        self.assertEqual(owner["event"], "owner_key_release_bracket")

    def test_rejects_wrong_owner_event(self):
        with self.assertRaisesRegex(ValueError, "owner_key_release_bracket"):
            join_explicit_release({"event": "owner_release"}, {})

    def test_rejects_caller_event_collision(self):
        with self.assertRaisesRegex(ValueError, "without event"):
            join_explicit_release({"event": "owner_key_release_bracket"}, {"event": "joined_release"})


if __name__ == "__main__":
    unittest.main()
