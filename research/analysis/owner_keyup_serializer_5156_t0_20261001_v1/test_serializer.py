import unittest

from serialize_release import join_explicit_release


class JoinedReleaseSerializationTests(unittest.TestCase):
    def test_nested_event_is_preserved_as_owner_event_and_joined_event_is_emitted(self):
        row = {
            "event": "owner_key_release_bracket",
            "case": "single_explicit",
            "key": "a",
            "keycode": 38,
            "owner_id": "owner-1",
            "intent_token": "intent-1",
            "request_started_ns": 10,
            "request_returned_ns": 11,
            "shared_sync_returned_ns": 12,
            "timing_valid": True,
            "grants_input_authority": False,
            "physical_key_up_claimed": False,
        }
        actual = join_explicit_release(
            row,
            {
                "case": "single_explicit",
                "caller_started_ns": 8,
                "caller_returned_ns": 14,
                "caller_owner_id": "owner-1",
                "caller_intent_token": "intent-1",
            },
        )
        self.assertEqual(actual["event"], "joined_release")
        self.assertEqual(actual["owner_event"], "owner_key_release_bracket")
        self.assertEqual(actual["keycode"], 38)
        self.assertEqual(actual["shared_sync_returned_ns"], 12)
        self.assertIs(actual["grants_input_authority"], False)
        self.assertIs(actual["physical_key_up_claimed"], False)
        self.assertEqual(actual["caller_started_ns"], 8)
        self.assertEqual(actual["caller_returned_ns"], 14)
        self.assertEqual(row["event"], "owner_key_release_bracket")

    def test_non_release_owner_records_are_refused(self):
        with self.assertRaisesRegex(ValueError, "owner_key_release_bracket"):
            join_explicit_release({"event": "owner_release"}, {"case": "single_explicit"})

    def test_caller_context_cannot_overwrite_event_provenance(self):
        with self.assertRaisesRegex(ValueError, "without event"):
            join_explicit_release(
                {"event": "owner_key_release_bracket"},
                {"case": "single_explicit", "event": "wrong"},
            )


if __name__ == "__main__":
    unittest.main(verbosity=2)
