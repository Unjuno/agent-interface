import unittest

from project_v39_release_measurement_v1 import project


def valid_pair():
    admission = {
        "event": "input_admission", "operation": "down", "key": "space",
        "id": "plan-a", "step": 2, "owner_id": "owner-1",
        "intent_token": "token-1", "admitted_ns": 100,
    }
    receipt = {
        "event": "owner_explicit_keyup", "operation": "up", "key": "space",
        "owner_id": "owner-1", "intent_token": "token-1",
        "valid_until_ns": 900,
        "owner_keyrelease_started_ns": 150,
        "owner_sync_returned_ns": 160, "owner_keymap_sampled_ns": 165,
        "server_sync_completed": True, "server_keyup_verified": True,
        "server_key_down_after_keyup": False, "key_state_source": "x11_query_keymap",
        "physical_verification_authoritative": False,
        "cancel_requested_after_sync": False,
        "server_keyup_attempt_count": 1,
        "server_keyup_attempts": [{"attempt": 1, "keyrelease_started_ns": 150,
            "sync_returned_ns": 160, "keymap_sampled_ns": 165,
            "server_key_down_before": True, "server_key_down_after": False}],
    }
    release = {
        "event": "input_release_transition", "operation": "up", "key": "space",
        "id": "plan-a", "step": 2, "owner_id": "owner-1",
        "intent_token": "token-1", "release_batch_identifier": "plan-a",
        "release_batch_step": 2, "release_batch_size": 1,
        "release_batch_position": 0, "release_batch_complete": True,
        "valid_until_ns": 900,
        "backend_owned_before_release": True, "ordinary_release_candidate": True,
        "release_call_started_ns": 140, "release_call_returned_ns": 170,
        "owner_thread_keyup_receipt": receipt,
        "owner_thread_keyup_receipt_count": 1,
        "owner_thread_keyup_history_complete": True,
        "owner_thread_keyup_verified": True, "owner_transition_verified": True,
        "owner_sample_after_batch_available": True,
        "owner_sample_after_started_ns": 180, "owner_sample_after_finished_ns": 185,
        "owned_keycodes_after_batch": [],
        "physical_verification_authoritative": False,
    }
    return [admission, release]


class StrictProjectionTests(unittest.TestCase):
    def test_projects_identity_bound_owner_release_without_claiming_app_consumption(self):
        result = project(valid_pair())
        self.assertTrue(result["measurement_ready"])
        row = result["rows"][0]
        self.assertEqual(row["event"], "input_release_measurement")
        self.assertEqual((row["id"], row["step"], row["key"], row["owner_id"],
                          row["intent_token"]),
                         ("plan-a", 2, "space", "owner-1", "token-1"))
        self.assertEqual(row["application_consumption"], "unobserved")

    def test_rejects_duplicate_owner_receipts_even_if_first_is_verified(self):
        records = valid_pair()
        records[1]["owner_thread_keyup_receipt_count"] = 2
        result = project(records)
        self.assertFalse(result["measurement_ready"])
        self.assertEqual(result["rows"], [])

    def test_rejects_boolean_receipt_count_and_owner_clock_reversal(self):
        records = valid_pair()
        records[1]["owner_thread_keyup_receipt_count"] = True
        self.assertFalse(project(records)["measurement_ready"])
        records = valid_pair()
        records[1]["owner_thread_keyup_receipt"]["owner_sync_returned_ns"] = 139
        self.assertFalse(project(records)["measurement_ready"])

    def test_rejects_missing_expiration_and_discontinuous_retry_state(self):
        records = valid_pair()
        del records[1]["valid_until_ns"]
        del records[1]["owner_thread_keyup_receipt"]["valid_until_ns"]
        self.assertFalse(project(records)["measurement_ready"])
        records = valid_pair()
        receipt = records[1]["owner_thread_keyup_receipt"]
        retry = {"attempt": 2, "keyrelease_started_ns": 166,
                 "sync_returned_ns": 168, "keymap_sampled_ns": 169,
                 "server_key_down_before": True, "server_key_down_after": False}
        receipt["server_keyup_attempts"].append(retry)
        receipt["server_keyup_attempt_count"] = 2
        receipt["owner_keyrelease_started_ns"] = 150
        receipt["owner_sync_returned_ns"] = 168
        receipt["owner_keymap_sampled_ns"] = 169
        records[1]["release_call_returned_ns"] = 175
        records[1]["owner_sample_after_started_ns"] = 180
        self.assertFalse(project(records)["measurement_ready"])

    def test_rejects_noncontiguous_multi_key_batch_positions(self):
        first = valid_pair()
        second = valid_pair()
        for rows, key, admitted, started, owner_started, owner_returned, sampled, returned, batch_pos in (
            (first, "space", 100, 140, 150, 160, 165, 170, 0),
            (second, "w", 101, 141, 151, 161, 166, 171, 2),
        ):
            admission, release = rows
            admission.update(key=key, admitted_ns=admitted)
            release.update(key=key, release_call_started_ns=started,
                           release_call_returned_ns=returned,
                           release_batch_position=batch_pos)
            receipt = release["owner_thread_keyup_receipt"]
            receipt.update(key=key, owner_keyrelease_started_ns=owner_started,
                           owner_sync_returned_ns=owner_returned,
                           owner_keymap_sampled_ns=sampled)
            attempt = receipt["server_keyup_attempts"][0]
            attempt.update(keyrelease_started_ns=owner_started,
                           sync_returned_ns=owner_returned,
                           keymap_sampled_ns=sampled)
        first[1].update(release_batch_size=2)
        second[1].update(release_batch_size=2)
        self.assertFalse(project(first + second)["measurement_ready"])


if __name__ == "__main__":
    unittest.main()
