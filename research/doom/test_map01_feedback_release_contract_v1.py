"""Boundary tests for conservative MAP01 feedback/release construction."""
import unittest

from map01_feedback_release_contract_v1 import (
    classify_useful_feedback, reconcile_key_intervals, recovery_window)


class FeedbackReleaseContractTests(unittest.TestCase):
    def observation(self, identifier, sequence, capture_ns):
        return {"event": "observation", "id": identifier, "sequence": sequence,
                "capture_ns": capture_ns, "exact": True,
                "pointer_binding": {"surface": 4, "geometry": [0, 0, 640, 480]}}

    def scorer(self, values, observation, sample_ns):
        return dict(values, sample_ns=sample_ns, independent=True,
                    controller_visible=False,
                    observation_id=observation["id"],
                    observation_sequence=observation["sequence"],
                    observation_capture_ns=observation["capture_ns"])

    def classify(self, before, after, *, before_override=None, after_override=None,
                 after_observation_override=None):
        # Runtime observation IDs can repeat within one program; sequence and
        # capture time complete the identity join.
        before_observation = self.observation("cover-0", 1, 10)
        after_observation = self.observation("cover-0", 2, 20)
        if after_observation_override:
            after_observation.update(after_observation_override)
        before_sample = self.scorer(before, before_observation, 11)
        after_sample = self.scorer(after, after_observation, 21)
        if before_override:
            before_sample.update(before_override)
        if after_override:
            after_sample.update(after_override)
        return classify_useful_feedback(
            before_sample, after_sample,
            before_observation=before_observation,
            after_observation=after_observation)

    def test_pairs_each_key_to_release_rpc_interval_not_exact_edge(self):
        def admission(step, key, ack):
            return {"event": "input_admission", "id": "plan", "step": step,
                    "key": key, "keycode": {"left": 37, "space": 65}[key],
                    "owner_id": "owner", "intent_token": "L1",
                    "admitted_ns": ack - 10, "input_ack_ns": ack}

        def release(step, key, start, end):
            return {"event": "input_release_rpc", "id": "plan", "step": step,
                    "payload": key, "owner_id": "owner", "intent_token": "L1",
                    "keycode": {"left": 37, "space": 65}[key],
                    "release_applied": True,
                    "operation": "up", "call_started_ns": start,
                    "call_returned_ns": end,
                    "release_transition_interval_ns": [start, end],
                    "interval_width_ns": end-start,
                    "x11_release_and_sync_completed_before_return": True,
                    "x11_release_request_issued": True,
                    "x11_sync_completed_before_return": True,
                    "continuous_physical_state_sampled": False,
                    "application_consumption_observed": False,
                    "grants_input_authority": False}
        events = [
            admission(0, "left", 110), admission(0, "space", 130),
            release(0, "left", 198, 200), release(0, "space", 218, 220),
        ]
        rows = reconcile_key_intervals(events)
        self.assertEqual([(r["id"], r["key"], r["occupancy_lower_ns"],
                           r["occupancy_upper_ns"], r["exact_key_up_time"],
                           r["censored"]) for r in rows],
                         [("plan", "left", 88, 90, None, False),
                          ("plan", "space", 88, 90, None, False)])

    def test_verified_empty_owner_release_censors_unclosed_key(self):
        rows = reconcile_key_intervals([
            {"event": "input_admission", "id": "L2", "step": 1, "key": "up",
             "owner_id": "owner", "intent_token": "L2", "admitted_ns": 300,
             "input_ack_ns": 310},
            {"event": "input_released", "intent_token": "L2",
             "grants_input_authority": False,
             "owner_release": {"event": "owner_release", "verified": True,
                               "keys_down": [], "buttons_down": [],
                               "verified_ns": 390}},
        ])
        self.assertEqual(rows, [{"intent_token": "L2", "id": "L2", "step": 1, "key": "up",
                                 "owner_id": "owner",
                                 "ack_ns": 310,
                                 "release_transition_interval_ns": None,
                                 "occupancy_lower_ns": None,
                                 "occupancy_upper_ns": 80,
                                 "exact_key_up_time": None, "censored": True}])

    def test_cancel_keycode_intervals_join_and_group_aliased_symbols(self):
        def admission(key, step, ack, code):
            return {"event": "input_admission", "id": "plan", "step": step,
                    "key": key, "keycode": code, "owner_id": "owner",
                    "intent_token": "alias-lease", "admitted_ns": ack-5,
                    "input_ack_ns": ack}

        release = {"event": "input_released", "intent_token": "alias-lease",
                   "grants_input_authority": False,
                   "owner_release": {"event": "owner_release", "verified": True,
                                     "keys_down": [], "buttons_down": [],
                                     "verified_ns": 390,
                                     "key_release_intervals_ns": [
                                         {"keycode": 77, "interval_ns": [350, 360]}]}}
        rows = reconcile_key_intervals([
            admission("W", 0, 310, 77), admission("A", 1, 320, 77), release])
        self.assertEqual(rows, [{"intent_token": "alias-lease", "owner_id": "owner",
                                 "id": "plan", "step": None, "key": None,
                                 "keys": ["A", "W"], "keycode": 77,
                                 "admission_count": 2, "ack_ns": 310,
                                 "release_transition_interval_ns": [350, 360],
                                 "occupancy_lower_ns": 40, "occupancy_upper_ns": 50,
                                 "exact_key_up_time": None, "censored": False}])

    def test_applied_ordinary_alias_release_groups_admissions_and_accepts_noop(self):
        def admission(key, step, ack):
            return {"event": "input_admission", "id": "plan", "step": step,
                    "key": key, "keycode": 77, "owner_id": "owner",
                    "intent_token": "alias-ordinary", "admitted_ns": ack-5,
                    "input_ack_ns": ack}

        common = {"event": "input_release_rpc", "id": "plan",
                  "owner_id": "owner", "intent_token": "alias-ordinary",
                  "operation": "up", "grants_input_authority": False,
                  "continuous_physical_state_sampled": False,
                  "application_consumption_observed": False}
        applied = dict(common, step=2, payload="W", keycode=77,
                       call_started_ns=350, call_returned_ns=360,
                       call_interval_ns=[350, 360], call_interval_width_ns=10,
                       release_transition_interval_ns=[350, 360], interval_width_ns=10,
                       release_applied=True, x11_release_request_issued=True,
                       x11_sync_completed_before_return=True,
                       x11_release_and_sync_completed_before_return=True)
        noop = dict(common, step=3, payload="A", keycode=77,
                    call_started_ns=370, call_returned_ns=380,
                    call_interval_ns=[370, 380], call_interval_width_ns=10,
                    release_transition_interval_ns=None, interval_width_ns=None,
                    release_applied=False, x11_release_request_issued=False,
                    x11_sync_completed_before_return=False,
                    x11_release_and_sync_completed_before_return=False)
        rows = reconcile_key_intervals([
            admission("W", 0, 310), admission("A", 1, 320), applied, noop])
        self.assertEqual(rows, [{"intent_token": "alias-ordinary", "owner_id": "owner",
                                 "id": "plan", "step": None, "key": None,
                                 "keys": ["A", "W"], "keycode": 77,
                                 "admission_count": 2, "ack_ns": 310,
                                 "release_transition_interval_ns": [350, 360],
                                 "occupancy_lower_ns": 40, "occupancy_upper_ns": 50,
                                 "exact_key_up_time": None, "censored": False}])

    def test_noop_keyup_without_admission_is_metadata_not_interval(self):
        noop = {"event": "input_release_rpc", "id": "plan", "step": 0,
                "payload": "A", "owner_id": "owner", "intent_token": "empty",
                "operation": "up", "keycode": 77, "release_applied": False,
                "call_started_ns": 10, "call_returned_ns": 15,
                "call_interval_ns": [10, 15], "call_interval_width_ns": 5,
                "release_transition_interval_ns": None, "interval_width_ns": None,
                "x11_release_request_issued": False,
                "x11_sync_completed_before_return": False,
                "x11_release_and_sync_completed_before_return": False,
                "continuous_physical_state_sampled": False,
                "application_consumption_observed": False,
                "grants_input_authority": False}
        self.assertEqual(reconcile_key_intervals([noop]), [])

    def test_noop_receipt_does_not_close_an_open_admission(self):
        admission = {"event": "input_admission", "id": "plan", "step": 0,
                     "key": "A", "keycode": 77, "owner_id": "owner",
                     "intent_token": "open-noop", "admitted_ns": 5,
                     "input_ack_ns": 10}
        noop = {"event": "input_release_rpc", "id": "plan", "step": 0,
                "payload": "A", "owner_id": "owner", "intent_token": "open-noop",
                "operation": "up", "keycode": 77, "release_applied": False,
                "call_started_ns": 15, "call_returned_ns": 20,
                "call_interval_ns": [15, 20], "call_interval_width_ns": 5,
                "release_transition_interval_ns": None, "interval_width_ns": None,
                "x11_release_request_issued": False,
                "x11_sync_completed_before_return": False,
                "x11_release_and_sync_completed_before_return": False,
                "continuous_physical_state_sampled": False,
                "application_consumption_observed": False,
                "grants_input_authority": False}
        with self.assertRaisesRegex(ValueError, "open_key_interval"):
            reconcile_key_intervals([admission, noop])

    def test_malformed_keycode_release_interval_fails_closed(self):
        admission = {"event": "input_admission", "id": "plan", "step": 0,
                     "key": "W", "keycode": 87, "owner_id": "owner",
                     "intent_token": "L7", "admitted_ns": 300, "input_ack_ns": 310}
        release = {"event": "input_released", "intent_token": "L7",
                   "grants_input_authority": False,
                   "owner_release": {"verified": True, "keys_down": [],
                                     "buttons_down": [], "verified_ns": 390,
                                     "key_release_intervals_ns": [
                                         {"keycode": 87, "interval_ns": [350, 400]}]}}
        with self.assertRaisesRegex(ValueError, "invalid_keycode_release_intervals"):
            reconcile_key_intervals([admission, release])

    def test_exact_observations_without_scored_change_are_not_useful_feedback(self):
        before = {"map_exit": False, "episode_finished": False, "player_dead": False,
                  "death_count": 0, "kill_count": 0}
        after = dict(before)
        self.assertEqual(self.classify(before, after), "no_scored_progress")

    def test_mismatched_or_controller_visible_scorer_evidence_is_unknown(self):
        before = {"map_exit": False, "episode_finished": False, "player_dead": False,
                  "death_count": 0, "kill_count": 0}
        after = dict(before, kill_count=1)
        self.assertEqual(self.classify(before, after,
                         after_override={"observation_id": "wrong-frame"}), "unknown")
        self.assertEqual(self.classify(before, after,
                         after_override={"controller_visible": True}), "unknown")
        self.assertEqual(self.classify(before, after,
                         after_override={"observation_sequence": 99}), "unknown")

    def test_nonchronological_or_rebound_observation_pair_is_unknown(self):
        before = {"map_exit": False, "episode_finished": False, "player_dead": False,
                  "death_count": 0, "kill_count": 0}
        after = dict(before, kill_count=1)
        self.assertEqual(self.classify(before, after,
                         after_observation_override={"sequence": 1}), "unknown")
        self.assertEqual(self.classify(before, after,
                         after_observation_override={"capture_ns": 9}), "unknown")
        self.assertEqual(self.classify(before, after,
                         after_observation_override={"pointer_binding": {"surface": 5}}),
                         "unknown")

    def test_scored_kill_and_exit_are_useful_progress(self):
        before = {"map_exit": False, "episode_finished": False, "player_dead": False,
                  "death_count": 0, "kill_count": 0}
        kill = dict(before, kill_count=1)
        exit_score = dict(kill, map_exit=True, episode_finished=True)
        self.assertEqual(self.classify(before, kill), "useful_progress")
        self.assertEqual(self.classify(kill, exit_score),
                         "useful_terminal_progress")
        unfinished_exit = dict(kill, episode_finished=True)
        self.assertEqual(self.classify(kill, unfinished_exit),
                         "adverse_progress")

    def test_adverse_progress_and_out_of_window_recovery_do_not_pass(self):
        before = {"map_exit": False, "episode_finished": False, "player_dead": False,
                  "death_count": 0, "kill_count": 1}
        dead = dict(before, player_dead=True, death_count=1)
        self.assertEqual(self.classify(before, dead),
                         "adverse_progress")
        self.assertFalse(recovery_window(100, 200, 201))
        self.assertTrue(recovery_window(100, 200, 200))

    def test_malformed_or_unpaired_physical_receipts_fail_closed(self):
        admitted = {"event": "input_admission", "id": "L3", "step": 0, "key": "x",
                    "keycode": 24,
                    "owner_id": "owner", "intent_token": "L3",
                    "admitted_ns": 500, "input_ack_ns": 510}
        wrong_step_release = {"event": "input_release_rpc", "id": "L3", "step": 1,
                         "payload": "x", "owner_id": "owner", "intent_token": "L3",
                         "keycode": 24, "release_applied": True,
                         "operation": "up", "call_started_ns": 520,
                         "call_returned_ns": 521,
                         "release_transition_interval_ns": [520, 521],
                         "interval_width_ns": 1,
                         "x11_release_and_sync_completed_before_return": True,
                         "x11_release_request_issued": True,
                         "x11_sync_completed_before_return": True,
                         "continuous_physical_state_sampled": False,
                         "application_consumption_observed": False,
                         "grants_input_authority": False}
        step_differs_from_admission = reconcile_key_intervals([admitted, wrong_step_release])
        self.assertEqual(step_differs_from_admission[0]["step"], 0)
        wrong_program_release = dict(wrong_step_release, id="different-program", step=0)
        with self.assertRaisesRegex(ValueError, "invalid_or_unmatched_release_rpc"):
            reconcile_key_intervals([admitted, wrong_program_release])
        wrong_keycode_release = dict(wrong_step_release, id="L3", step=0, keycode=25)
        with self.assertRaisesRegex(ValueError, "invalid_or_unmatched_release_rpc"):
            reconcile_key_intervals([admitted, wrong_keycode_release])
        noop_release = dict(wrong_step_release, id="L3", step=0,
                            release_applied=False)
        with self.assertRaisesRegex(ValueError, "invalid_or_unmatched_release_rpc"):
            reconcile_key_intervals([admitted, noop_release])
        unproven_release = dict(wrong_step_release, id="L3", step=0)
        unproven_release.pop("keycode")
        unproven_release.pop("release_applied")
        with self.assertRaisesRegex(ValueError, "invalid_or_unmatched_release_rpc"):
            reconcile_key_intervals([admitted, unproven_release])
        unproven_io = dict(wrong_step_release, id="L3", step=0)
        unproven_io.pop("x11_sync_completed_before_return")
        with self.assertRaisesRegex(ValueError, "invalid_or_unmatched_release_rpc"):
            reconcile_key_intervals([admitted, unproven_io])
        with self.assertRaisesRegex(ValueError, "open_key_interval"):
            reconcile_key_intervals([admitted])
        with self.assertRaisesRegex(ValueError, "unverified_owner_release"):
            reconcile_key_intervals([dict(admitted, id="L4", intent_token="L4"),
                {"event": "input_released", "intent_token": "L4",
                 "grants_input_authority": False,
                 "owner_release": {"event": "owner_release", "verified": False,
                                   "keys_down": ["x"], "buttons_down": [],
                                   "verified_ns": 530}}])
        with self.assertRaisesRegex(ValueError, "unverified_owner_release"):
            reconcile_key_intervals([dict(admitted, id="L5", intent_token="L5"),
                {"event": "owner_release", "intent_token": "L5", "verified": True,
                 "keys_down": [], "buttons_down": [], "verified_ns": 530}])
        with self.assertRaisesRegex(ValueError, "unverified_owner_release"):
            reconcile_key_intervals([dict(admitted, id="L6", intent_token="L6"),
                {"event": "input_released", "intent_token": "L6",
                 "grants_input_authority": True,
                 "owner_release": {"event": "owner_release", "verified": True,
                                   "keys_down": [], "buttons_down": [],
                                   "verified_ns": 530}}])

    def test_retained_v39_admission_shape_cannot_be_misreported_as_interval_data(self):
        raw_v39_admission = {"event": "input_admission", "key": "Up",
                             "admitted_ns": 55510744310481,
                             "input_ack_ns": 55510744604148,
                             "valid_until_ns": 55535713001369,
                             "emit_ns": 55510744688125}
        with self.assertRaisesRegex(ValueError, "invalid_admission"):
            reconcile_key_intervals([raw_v39_admission])


if __name__ == "__main__":
    unittest.main()
