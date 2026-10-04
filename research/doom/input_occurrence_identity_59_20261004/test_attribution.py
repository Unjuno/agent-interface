import unittest

from attribution import attribute_progress_events, normalize_releases


def fixture():
    admission = {
        "event": "input_admission", "id": "program-1", "step": 2,
        "key": "W", "keycode": 38, "input_occurrence_id": "owner-a:9",
        "owner_id": "owner-a", "intent_token": "intent-a",
        "admitted_ns": 100, "input_ack_ns": 110,
    }
    release = {
        "event": "input_release_transition", "id": "program-1", "step": 2,
        "owner_thread_keyup_receipt": {
            "event": "owner_explicit_keyup", "keycode": 38,
            "input_occurrence_id": "owner-a:9", "owner_id": "owner-a",
            "intent_token": "intent-a", "owner_keyrelease_started_ns": 200,
            "owner_sync_returned_ns": 210, "server_sync_completed": True,
            "cancel_requested_after_sync": False,
        },
    }
    event = {"schema": "independent-progress-event-v2", "event_sequence": 1,
             "observed_ns": 150, "kind": "KILL_COUNT_INCREASE",
             "controller_visible": False}
    binding = {"program_id": "program-1", "step": 2,
               "semantic_action_sha256": "a" * 64}
    return admission, release, event, binding


class AttributionTests(unittest.TestCase):
    def test_unique_event_to_action_and_owner_release(self):
        admission, raw_release, event, binding = fixture()
        releases = normalize_releases([raw_release])
        result = attribute_progress_events([event], [admission], releases,
                                           [binding])[0]
        self.assertEqual(result["status"], "unique_temporal_occurrence")
        self.assertEqual(result["input_occurrence_id"], "owner-a:9")
        self.assertFalse(result["causation_claimed"])

    def test_release_sync_window_is_not_claimed_as_active(self):
        admission, raw_release, event, binding = fixture()
        event["observed_ns"] = 205
        result = attribute_progress_events([event], [admission],
                                           normalize_releases([raw_release]),
                                           [binding])[0]
        self.assertEqual(result["status"], "unresolved_release_boundary")

    def test_cancellation_batch_interval_keeps_occurrence_identity(self):
        admission, _raw_release, event, binding = fixture()
        cancellation = {
            "event": "input_released", "id": "program-1",
            "owner_release": {
                "event": "owner_release", "verified": True,
                "key_release_intervals_ns": [{
                    "keycode": 38, "input_occurrence_id": "owner-a:9",
                    "owner_id": "owner-a", "intent_token": "intent-a",
                    "interval_ns": [200, 210],
                }],
            },
        }
        result = attribute_progress_events(
            [event], [admission], normalize_releases([cancellation]),
            [binding])[0]
        self.assertEqual(result["status"], "unique_temporal_occurrence")

    def test_two_active_key_occurrences_are_ambiguous(self):
        admission, raw_release, event, binding = fixture()
        second = dict(admission, key="A", keycode=39,
                      input_occurrence_id="owner-a:10")
        second_release = dict(raw_release,
                              owner_thread_keyup_receipt=dict(
                                  raw_release["owner_thread_keyup_receipt"],
                                  keycode=39, input_occurrence_id="owner-a:10"))
        result = attribute_progress_events(
            [event], [admission, second],
            normalize_releases([raw_release, second_release]),
            [binding])[0]
        self.assertEqual(result["status"], "ambiguous_multiple_active_occurrences")

    def test_missing_or_duplicate_release_fails_closed(self):
        admission, raw_release, event, binding = fixture()
        release = normalize_releases([raw_release])[0]
        for releases in ([], [release, release]):
            result = attribute_progress_events([event], [admission], releases,
                                               [binding])[0]
            self.assertEqual(result["status"],
                             "unresolved_invalid_or_nonunique_lifecycle")

    def test_missing_or_ambiguous_action_binding_fails_closed(self):
        admission, raw_release, event, binding = fixture()
        releases = normalize_releases([raw_release])
        invalid_hash = dict(binding, semantic_action_sha256="not-a-sha256")
        for bindings in ([], [binding, binding], [invalid_hash]):
            result = attribute_progress_events([event], [admission], releases,
                                               bindings)[0]
            self.assertEqual(result["status"],
                             "unresolved_invalid_or_nonunique_lifecycle")

    def test_identity_mismatch_and_controller_visible_event_fail_closed(self):
        admission, raw_release, event, binding = fixture()
        raw_release["owner_thread_keyup_receipt"]["input_occurrence_id"] = "owner-a:10"
        result = attribute_progress_events([event], [admission],
                                           normalize_releases([raw_release]),
                                           [binding])[0]
        self.assertEqual(result["status"],
                         "unresolved_invalid_or_nonunique_lifecycle")
        event["controller_visible"] = True
        result = attribute_progress_events([event], [admission], [], [binding])[0]
        self.assertEqual(result["status"], "unresolved_invalid_progress_event")


if __name__ == "__main__":
    unittest.main()
