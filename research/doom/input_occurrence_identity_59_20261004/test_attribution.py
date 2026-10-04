import unittest

from attribution import attribute_positive_events, normalize_releases


def fixture():
    samples = [
        {"schema": "independent-progress-sample-v2", "session_id": "session-a",
         "sample_ns": 100, "kill_count": 0, "death_count": 0},
        {"schema": "independent-progress-sample-v2", "session_id": "session-a",
         "sample_ns": 200, "kill_count": 1, "death_count": 0},
    ]
    events = [{"schema": "independent-progress-event-v2", "session_id": "session-a",
               "event_sequence": 1, "observed_ns": 200,
               "kind": "KILL_COUNT_INCREASE", "polarity": "positive",
               "useful": True, "controller_visible": False}]
    admission = {
        "event": "input_admission", "session_id": "session-a",
        "id": "program-1", "step": 2, "key": "W", "keycode": 38,
        "input_occurrence_id": "owner-a:9", "owner_id": "owner-a",
        "intent_token": "intent-a", "admitted_ns": 80, "input_ack_ns": 90,
    }
    release = {
        "event": "input_release_transition", "session_id": "session-a",
        "id": "program-1", "step": 2,
        "owner_thread_keyup_receipt": {
            "event": "owner_explicit_keyup", "key": "W", "keycode": 38,
            "input_occurrence_id": "owner-a:9", "owner_id": "owner-a",
            "intent_token": "intent-a", "owner_keyrelease_started_ns": 210,
            "owner_sync_returned_ns": 220, "server_sync_completed": True,
            "cancel_requested_after_sync": False,
        },
    }
    binding = {"session_id": "session-a", "program_id": "program-1", "step": 2,
               "semantic_action_sha256": "a" * 64}
    return samples, events, admission, release, binding


class AttributionTests(unittest.TestCase):
    def test_strict_full_detection_bracket_is_only_a_possible_envelope(self):
        samples, events, admission, release, binding = fixture()
        result = attribute_positive_events(
            samples, events, [admission], normalize_releases([release]),
            [binding])[0]
        self.assertEqual(result["detection_interval_ns"], [100, 200])
        self.assertEqual(result["status"], "SINGLE_POSSIBLE_INTENT_ENVELOPE")
        self.assertIsNone(result["intent_token"])
        self.assertEqual(result["possible_occurrence_ids"], ["owner-a:9"])
        self.assertEqual(result["causal_attribution"], "NOT_ESTABLISHED")

    def test_instantaneous_timestamp_inside_interval_does_not_cover_detection_bracket(self):
        samples, events, admission, release, binding = fixture()
        release["owner_thread_keyup_receipt"]["owner_keyrelease_started_ns"] = 150
        release["owner_thread_keyup_receipt"]["owner_sync_returned_ns"] = 160
        result = attribute_positive_events(
            samples, events, [admission], normalize_releases([release]),
            [binding])[0]
        self.assertEqual(result["status"], "UNRESOLVED")
        self.assertEqual(result["reason"], "no_complete_verified_intent_coverage")

    def test_cross_session_rows_are_rejected(self):
        samples, events, admission, release, binding = fixture()
        events[0]["session_id"] = "session-b"
        with self.assertRaisesRegex(ValueError, "session_id mismatch"):
            attribute_positive_events(samples, events, [admission],
                                     normalize_releases([release]), [binding])

    def test_endpoint_tie_is_unresolved(self):
        samples, events, admission, release, binding = fixture()
        release["owner_thread_keyup_receipt"]["owner_keyrelease_started_ns"] = 190
        release["owner_thread_keyup_receipt"]["owner_sync_returned_ns"] = 200
        result = attribute_positive_events(
            samples, events, [admission], normalize_releases([release]),
            [binding])[0]
        self.assertEqual(result["status"], "UNRESOLVED")
        self.assertEqual(result["reason"], "endpoint_tie_without_authenticated_order")

    def test_multiple_intents_are_ambiguous(self):
        samples, events, admission, release, binding = fixture()
        second = dict(admission, id="program-2", input_occurrence_id="owner-a:10",
                      intent_token="intent-b", key="A", keycode=39)
        second_release = dict(release, id="program-2", owner_thread_keyup_receipt=dict(
            release["owner_thread_keyup_receipt"], input_occurrence_id="owner-a:10",
            intent_token="intent-b", key="A", keycode=39))
        second_binding = dict(binding, program_id="program-2",
                              semantic_action_sha256="b" * 64)
        result = attribute_positive_events(
            samples, events, [admission, second],
            normalize_releases([release, second_release]),
            [binding, second_binding])[0]
        self.assertEqual(result["status"], "AMBIGUOUS")
        self.assertEqual(result["possible_intent_tokens"], ["intent-a", "intent-b"])

    def test_unverified_cancel_release_stays_unresolved(self):
        samples, events, admission, _release, binding = fixture()
        cancel = {"event": "input_released", "session_id": "session-a",
                  "id": "program-1", "owner_release": {
                      "event": "owner_release", "verified": False,
                      "key_release_intervals_ns": [{
                          "keycode": 38, "input_occurrence_id": "owner-a:9",
                          "owner_id": "owner-a", "intent_token": "intent-a",
                          "interval_ns": [150, 220],
                      }],
                  }}
        result = attribute_positive_events(
            samples, events, [admission], normalize_releases([cancel]),
            [binding])[0]
        self.assertEqual(result["status"], "UNRESOLVED")
        self.assertEqual(result["reason"], "unverified_release_boundary")

    def test_missing_duplicate_or_mismatched_occurrence_fails_closed(self):
        samples, events, admission, release, binding = fixture()
        normalized = normalize_releases([release])
        for admissions, releases in (([admission], []),
                                     ([admission, admission], normalized),
                                     ([admission], normalized + normalized)):
            with self.assertRaises(ValueError):
                attribute_positive_events(samples, events, admissions, releases,
                                          [binding])
        release["owner_thread_keyup_receipt"]["input_occurrence_id"] = "other"
        with self.assertRaisesRegex(ValueError, "requires exactly one release"):
            attribute_positive_events(samples, events, [admission],
                                      normalize_releases([release]), [binding])


if __name__ == "__main__":
    unittest.main()
