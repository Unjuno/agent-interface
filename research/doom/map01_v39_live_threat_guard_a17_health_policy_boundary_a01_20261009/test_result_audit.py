import unittest

from audit_a17_health_guard_result import classify, collect_action_health_rejections


def rejection(fingerprint, source, fresh, maximum, sequence):
    return {
        "status": "REJECTED_PREDICATE",
        "reason": "health_max_decrease_from_source_failed",
        "contract": {
            "action_fingerprint": fingerprint,
            "source": {"signals": {"health": {"value": source}}},
        },
        "snapshot": {"sequence": sequence, "signals": {"health": {"value": fresh}}},
        "checks": [{"signal_id": "health", "operator": "max_decrease_from_source",
                    "expected": maximum, "observed": fresh, "passed": False}],
    }


class A17ResultAuditTests(unittest.TestCase):
    def test_action_receipts_deduplicate_and_preserve_lifecycle_stage(self):
        revoked = rejection("a", 97, 85, 10, 44)
        rejected = rejection("b", 85, 70, 8, 65)
        report = {"decisions": [
            {"iteration": 1,
             "running_action_guard": {"invalidation": revoked,
                                      "running_validity": {"invalidation": revoked}}},
            {"iteration": 2,
             "final_action_admission": {"action_validity": rejected}},
        ]}
        rows = collect_action_health_rejections(report)
        self.assertEqual([(r["decision_iteration"], r["outcome"]) for r in rows],
                         [(1, "revoked_after_executor_acceptance"),
                          (2, "rejected_before_executor_admission")])

    def test_unexposed_preregistered_guard_stays_hold(self):
        checks = {key: True for key in (
            "allocation_identity", "source_commit_is_verified_prelaunch_main",
            "runtime_source_closure_is_complete_and_frozen",
            "all_runtime_sources_match_local_and_frozen_main",
            "guest_host_source_mapping_is_frozen", "known_startup_dependencies_are_frozen",
            "no_preexisting_game_or_display_process", "runner_and_auditor_hashes_match_freeze",
            "fixture_hashes_match_freeze", "qualified_wad_hash_matches",
            "forwarded_images_host_receipts_valid", "all_accepted_programs_have_terminals",
            "per_key_release_rows_accounted", "terminal_releases_verified_empty",
            "no_stale_admission_after_guard")}
        audit = {"checks": checks, "controller_failure": None}
        custody = {"custody_pass": True}
        censor = {"hard_health_guard_count": 0,
                  "classifications": {"recovered_within_two_decisions": 0,
                                      "observable_recovery_missed": 0}}
        self.assertEqual(classify(audit, custody, censor)[0], "HOLD")


if __name__ == "__main__":
    unittest.main()
