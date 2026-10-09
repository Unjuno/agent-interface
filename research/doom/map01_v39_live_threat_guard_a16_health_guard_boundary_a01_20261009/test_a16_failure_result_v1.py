import unittest

from audit_a16_failure_result_v1 import build_result


class A16FailureResultTests(unittest.TestCase):
    def setUp(self):
        self.freeze = {"runtime": {"iterations": 24}, "source_hashes": {
            "research/doom/doom_signal_value_domain_v1.py": "abc123"}}
        self.audit = {
            "status": "STOP",
            "checks": {
                "allocation_identity": True,
                "source_commit_is_verified_prelaunch_main": True,
                "runtime_source_closure_is_complete_and_frozen": True,
                "all_runtime_sources_match_local_and_frozen_main": True,
                "guest_host_source_mapping_is_frozen": True,
                "known_startup_dependencies_are_frozen": True,
                "no_preexisting_game_or_display_process": True,
                "runner_and_auditor_hashes_match_freeze": True,
                "fixture_hashes_match_freeze": True,
                "qualified_wad_hash_matches": True,
                "forwarded_images_host_receipts_valid": True,
                "all_accepted_programs_have_terminals": True,
                "cancellation_custody_reconciled": True,
                "per_key_release_rows_accounted": True,
                "terminal_releases_verified_empty": True,
                "no_stale_admission_after_guard": True,
            },
            "counts": {"hard_health_guard_exposures": 0,
                       "useful_events_during_model_wait": 0,
                       "model_turns_started": 12,
                       "model_turns_completed": 12},
            "health_values": [0, 75, 100], "ammo_values": [40, 50],
        }
        self.custody = {
            "custody_pass": True, "matched_cancellations": 12,
            "accounted_cancellations": 12, "unaccounted_cancellations": 0,
            "per_key_release_transitions": 32,
            "owner_keyups_matching_key_and_token": 32,
            "terminals": 16, "terminals_with_verified_empty_release": 16,
        }
        self.host = {"guest_exit": 1, "app_server_exit": 0,
                     "retry_count": 0, "elapsed_seconds": 71}
        self.score = {"kill_count": 1, "death_count": 1, "player_dead": True,
                      "map_exit": False, "episode_finished": True}
        self.failure = {"primary_error_type": "SourceRefreshRefused",
                        "failed_stage": "source_refresh", "cleanup_complete": False,
                        "input_terminals_complete": True,
                        "input_releases_verified_empty": False,
                        "owner_events_closed": False}
        self.refresh = {"iteration": 12, "source_sequence": 338,
                        "reason": "invalid_observed_health"}
        self.events = [{"event": "typed_observation", "sequence": 325,
                        "signals": {"health": {"status": "observed", "value": 0}}}]
        self.owner_rows = [
            {"event": "owner_explicit_keyup", "server_keyup_verified": True,
             "server_sync_completed": True, "server_key_down_after_keyup": False},
            {"event": "owner_release", "reason": "close", "verified": True,
             "keys_down": [], "buttons_down": [], "keys_unknown": [],
             "key_state_errors": []},
        ]

    def test_missing_report_and_death_remain_scoped_stop(self):
        result = build_result(self.freeze, self.audit, self.custody, self.host,
                              self.score, self.failure, self.refresh,
                              self.events, self.owner_rows,
                              report_present=False)
        self.assertEqual(result["status"], "STOP")
        self.assertEqual(result["hard_health_guard_count"], 0)
        self.assertFalse(result["decision_report_present"])
        self.assertFalse(result["controller_failure"]["cleanup_complete"])
        self.assertEqual(result["source_refresh_failure"]["reason"],
                         "invalid_observed_health")
        self.assertTrue(result["owner_event_log_reconciled_by_event_schema"]["closed"])
        self.assertEqual(result["observed_health_zero"]["sequence"], 325)
        self.assertEqual(result["signal_domain_source"]["sha256"], "abc123")
        self.assertEqual(result["final_model_decision"]["response"][
            "next_cover_validity"]["critical_health_minimum"], 1)
        self.assertIn("does not establish", result["final_model_decision"][
            "interpretation"])

    def test_missing_report_cannot_be_mislabeled_as_complete(self):
        self.audit["checks"]["terminal_releases_verified_empty"] = False
        result = build_result(self.freeze, self.audit, self.custody, self.host,
                              self.score, self.failure, self.refresh,
                              self.events, self.owner_rows,
                              report_present=False)
        self.assertEqual(result["status"], "FAIL")

    def test_sequence_and_health_join_must_match_frozen_failure(self):
        self.refresh["source_sequence"] = 337
        result = build_result(self.freeze, self.audit, self.custody, self.host,
                              self.score, self.failure, self.refresh,
                              self.events, self.owner_rows,
                              report_present=False)
        self.assertEqual(result["status"], "FAIL")

    def test_failure_reconciler_refuses_to_replace_a_present_report(self):
        with self.assertRaises(ValueError):
            build_result(self.freeze, self.audit, self.custody, self.host,
                          self.score, self.failure, self.refresh,
                          self.events, self.owner_rows,
                          report_present=True)

    def test_unverified_owner_keyup_fails_closed(self):
        self.owner_rows[0]["server_keyup_verified"] = False
        result = build_result(self.freeze, self.audit, self.custody, self.host,
                              self.score, self.failure, self.refresh,
                              self.events, self.owner_rows,
                              report_present=False)
        self.assertEqual(result["status"], "FAIL")

    def test_owner_release_key_state_errors_fail_closed(self):
        for errors in (["readback failed"], None):
            with self.subTest(errors=errors):
                if errors is None:
                    self.owner_rows[1].pop("key_state_errors")
                else:
                    self.owner_rows[1]["key_state_errors"] = errors
                result = build_result(self.freeze, self.audit, self.custody,
                                      self.host, self.score, self.failure,
                                      self.refresh, self.events, self.owner_rows,
                                      report_present=False)
                self.assertEqual(result["status"], "FAIL")
                self.assertFalse(result[
                    "owner_event_log_reconciled_by_event_schema"]["closed"])


if __name__ == "__main__":
    unittest.main()
