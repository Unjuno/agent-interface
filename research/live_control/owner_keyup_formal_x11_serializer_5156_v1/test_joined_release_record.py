import json
import unittest

from release_serialization import joined_release_record


class JoinedReleaseRecordTests(unittest.TestCase):
    def test_original_expression_reproduces_the_duplicate_keyword_failure(self):
        row = {"event": "owner_key_release_bracket", "key": "a"}
        with self.assertRaisesRegex(TypeError, "multiple values for keyword argument 'event'"):
            dict(event="joined_release", **row)

    def test_existing_owner_event_is_replaced_without_keyword_collision(self):
        row = {"event": "owner_key_release_bracket", "key": "a", "owner_id": "o1"}
        result = joined_release_record(row)
        self.assertEqual(result, {"event": "joined_release", "key": "a", "owner_id": "o1"})

    def test_missing_event_is_added(self):
        self.assertEqual(joined_release_record({"key": "b"}),
                         {"event": "joined_release", "key": "b"})

    def test_source_row_is_not_mutated(self):
        row = {"event": "owner_key_release_bracket", "key": "a"}
        joined_release_record(row)
        self.assertEqual(row["event"], "owner_key_release_bracket")

    def test_joined_row_remains_json_serializable_and_keeps_measurements(self):
        row = {"event": "owner_key_release_bracket", "key": "a",
               "release_started_ns": 10, "sync_returned_ns": 12}
        decoded = json.loads(json.dumps(joined_release_record(row)))
        self.assertEqual(decoded["event"], "joined_release")
        self.assertEqual((decoded["release_started_ns"], decoded["sync_returned_ns"]), (10, 12))


if __name__ == "__main__":
    unittest.main()
