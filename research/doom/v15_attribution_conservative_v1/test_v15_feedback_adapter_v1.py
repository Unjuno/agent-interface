import copy
import unittest
from v15_feedback_adapter_v1 import adapt_session_records
def sample(ns, kills):
    return {
        "scheduled_ns": ns, "sample_started_ns": ns, "sample_finished_ns": ns,
        "start_lateness_ns": 0, "missed_periods_before": 0,
        "payload": {"schema":"independent-progress-sample-v2", "sample_ns":ns,
                    "kill_count":kills, "death_count":0, "episode_finished":False,
                    "player_dead":False, "map_exit":False},
        "controller_visible":False,
    }

def event(ns=300):
    return {"schema":"independent-progress-event-v2", "event_sequence":1,
            "observed_ns":ns, "kind":"KILL_COUNT_INCREASE", "polarity":"positive",
            "useful":True, "controller_visible":False,
            "before":{"kill_count":0}, "after":{"kill_count":1,"delta":1}}

def valid_pair():
    admission = {
        "event": "input_admission", "operation": "down", "key": "space",
        "id": "plan-a", "step": 2, "owner_id": "owner-1",
        "intent_token": "token-1", "admitted_ns": 100,
        "input_ack_ns": 110, "valid_until_ns": 900,
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
        "release_batch_initial_up_count": 1,
        "release_batch_key_order": ["space"],
        "server_keyup_attempt_count": 1,
        "server_keyup_attempts": [{"attempt": 1, "keyrelease_started_ns": 150,
            "sync_returned_ns": 160, "keymap_sampled_ns": 165,
            "server_key_down_before": True, "server_key_down_after": False,
            "keyrelease_error": None, "sync_error": None,
            "keymap_before_error": None, "keymap_after_error": None}],
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
        "release_batch_schema": "input-release-batch-v3",
        "owner_sample_ordered_after_batch": True,
        "owner_identity_matches_after_batch": True,
        "intent_token_matches_after_batch": True,
        "owner_thread_keyup_verified_after_batch": True,
        "owner_sample_after_started_ns": 180, "owner_sample_after_finished_ns": 185,
        "owned_keycodes_after_batch": [],
        "physical_verification_authoritative": False,
    }
    return [admission, release]

class ConservativeCompositionTests(unittest.TestCase):
    def run_case(self, rows):
        return adapt_session_records([sample(130, 0), sample(150, 1)], [event(150)], rows)["attributions"][0]

    def test_verified_endpoints_are_only_a_possible_envelope(self):
        result = self.run_case(valid_pair())
        self.assertEqual(result["status"], "SINGLE_POSSIBLE_INTENT_ENVELOPE")
        self.assertIsNone(result["intent_token"])
        self.assertEqual(result["causal_attribution"], "NOT_ESTABLISHED")

    def test_release_call_failure_remains_unresolved(self):
        rows = valid_pair()
        rows[1]["owner_thread_keyup_receipt"]["server_keyup_attempts"][0]["keyrelease_error"] = {"type": "OSError"}
        result = self.run_case(rows)
        self.assertEqual(result["status"], "UNRESOLVED")
        self.assertIsNone(result["intent_token"])

    def test_measured_competitor_remains_ambiguous(self):
        rows = valid_pair()
        rows.append(dict(program_id_sha256="a"*64, owner_id_sha256="b"*64,
            intent_token_sha256="c"*64, key="x", step=0,
            status="adapter_edge_brackets_paired", down_edge_interval_ns=[125, 135],
            up_edge_interval_ns=[145, 155], grants_input_authority=False,
            application_consumption_observed=False))
        result = self.run_case(rows)
        self.assertEqual(result["status"], "AMBIGUOUS")
        self.assertEqual(len(result["possible_intent_token_sha256"]), 2)
        self.assertIsNone(result["intent_token"])


    def test_missing_error_evidence_cannot_support_an_envelope(self):
        rows = valid_pair()
        del rows[1]["owner_thread_keyup_receipt"]["server_keyup_attempts"][0]["sync_error"]
        result = self.run_case(rows)
        self.assertEqual(result["status"], "UNRESOLVED")
        self.assertIsNone(result["intent_token"])

    def test_unknown_positive_event_is_rejected(self):
        e = event(150)
        e["kind"] = "UNREGISTERED_POSITIVE"
        with self.assertRaises(ValueError):
            adapt_session_records([sample(130, 0), sample(150, 1)], [e], valid_pair())

    def test_incomplete_row_suppresses_unique_attribution(self):
        rows = valid_pair()
        rows[1]["release_batch_complete"] = False
        result = self.run_case(rows)
        self.assertEqual(result["status"], "UNRESOLVED")
        self.assertIsNone(result["intent_token"])


class ProducerCompositionTests(unittest.TestCase):
    def test_actual_fake_xlib_batch_remains_a_possible_envelope(self):
        from test_project_v39_release_measurement_composition import ProducerProjectionTests
        fixture = ProducerProjectionTests(methodName="runTest")
        self.addCleanup(fixture.doCleanups)
        fixture.setUp()
        self.assertTrue(fixture.run_batch()["measurement_ready"])
        admissions = [row for row in fixture.events if row.get("event") == "input_admission"]
        releases = [row for row in fixture.events if row.get("event") == "input_release_transition"]
        start = max(row["admitted_ns"] for row in admissions)
        end = min(row["owner_thread_keyup_receipt"]["owner_sync_returned_ns"] for row in releases)
        self.assertGreater(end - start, 3)
        lower = start + 1
        upper = end - 1
        result = adapt_session_records([sample(lower, 0), sample(upper, 1)],
                                       [event(upper)], fixture.events)
        self.assertEqual(result["trace_integrity"], "SOURCE_ROWS_JOINED")
        row = result["attributions"][0]
        self.assertEqual(row["status"], "SINGLE_POSSIBLE_INTENT_ENVELOPE")
        self.assertIsNone(row["intent_token"])
        self.assertEqual(row["causal_attribution"], "NOT_ESTABLISHED")

    def test_actual_failed_keyup_does_not_prove_an_envelope(self):
        from test_project_v39_release_measurement_composition import ProducerProjectionTests
        fixture = ProducerProjectionTests(methodName="runTest")
        self.addCleanup(fixture.doCleanups)
        fixture.setUp()
        fixture.fake.fail_after_keyup = True
        self.assertEqual(fixture.run_batch(), {"measurement_ready": False, "rows": []})
        admissions = [row for row in fixture.events if row.get("event") == "input_admission"]
        releases = [row for row in fixture.events if row.get("event") == "input_release_transition"]
        start = max(row["admitted_ns"] for row in admissions)
        end = min(row["owner_thread_keyup_receipt"]["owner_sync_returned_ns"] for row in releases)
        self.assertGreater(end - start, 3)
        lower, upper = start + 1, end - 1
        result = adapt_session_records([sample(lower, 0), sample(upper, 1)],
                                       [event(upper)], fixture.events)
        self.assertEqual(result["trace_integrity"], "SOURCE_ROWS_UNVERIFIED")
        row = result["attributions"][0]
        self.assertEqual(row["status"], "UNRESOLVED")
        self.assertIsNone(row["intent_token"])
        self.assertEqual(row["causal_attribution"], "NOT_ESTABLISHED")

if __name__ == "__main__": unittest.main()
