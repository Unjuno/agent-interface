from __future__ import annotations

import unittest

import auditor
import build_model
import candidate


class DegradationConstructionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model = build_model.build()
        cls.result = candidate.build_result(cls.model)

    def test_complete_exhaustive_matrix(self):
        scenarios = self.model["scenarios"]
        self.assertEqual(len(scenarios), 1024)
        self.assertEqual(len({s["scenario_id"] for s in scenarios}), 1024)
        self.assertEqual(len({tuple(s["available_services"].values()) + (
            s["authority_granted"], s["release_channel_available"], s["evidence_fresh"],
            bool(s["pending_release_ids"])
        ) for s in scenarios}), 1024)

    def test_full_contract_admits_but_does_not_execute_action(self):
        row = next(
            r for r in self.result["cases"]
            if all(r["available_services"].values()) and r["authority_granted"]
            and r["release_channel_available"] and r["evidence_fresh"]
            and not r["pending_release_ids"]
        )
        self.assertEqual(row["mode"], "FULL_V1")
        self.assertIn("admit_reversible_action", row["admissible_operations"])
        self.assertEqual(row["claim_ceiling_by_operation"]["admit_reversible_action"], "ACTION_ADMITTED")
        self.assertNotIn("TASK_EFFECT", row["claim_ceiling_by_operation"].values())

    def test_noncritical_failure_preserves_scoped_reads(self):
        scenario = next(
            s for s in self.model["scenarios"]
            if not s["available_services"]["planner"]
            and s["available_services"]["raw_observer"]
            and s["evidence_fresh"]
        )
        row = candidate.classify(scenario)
        self.assertEqual(row["mode"], "READ_ONLY_V1")
        self.assertIn("read_raw", row["admissible_operations"])
        self.assertNotIn("admit_reversible_action", row["admissible_operations"])

    def test_stale_authority_and_release_failures_fail_closed(self):
        scenario = next(
            s for s in self.model["scenarios"]
            if s["available_services"]["raw_observer"] and not s["evidence_fresh"]
        )
        self.assertEqual(candidate.classify(scenario)["admissible_operations"], [])
        action_scenario = next(
            s for s in self.model["scenarios"]
            if s["authority_granted"] and not s["release_channel_available"]
            and all(s["available_services"].values()) and s["evidence_fresh"]
            and not s["pending_release_ids"]
        )
        self.assertNotIn("admit_reversible_action", candidate.classify(action_scenario)["admissible_operations"])

    def test_pending_release_is_preserved_and_blocks_new_action(self):
        scenario = next(s for s in self.model["scenarios"] if s["pending_release_ids"])
        row = candidate.classify(scenario)
        self.assertEqual(row["pending_release_ids"], ["lease-01"])
        self.assertNotIn("admit_reversible_action", row["admissible_operations"])
        no_release = next(
            s for s in self.model["scenarios"]
            if s["pending_release_ids"] and not s["release_channel_available"]
        )
        no_release_row = candidate.classify(no_release)
        self.assertEqual(no_release_row["pending_release_ids"], ["lease-01"])
        self.assertFalse(no_release_row["release_action_eligible"])

    def test_independent_audit_reconstructs_matrix(self):
        errors = auditor.audit_rows(self.model, self.result, "8609-T0-A01-20261009")
        self.assertEqual(errors, [])

    def test_all_frozen_corruptions_are_rejected(self):
        probes = auditor.mutation_probes(self.model, self.result, "8609-T0-A01-20261009")
        self.assertEqual(probes, [True] * 6)


if __name__ == "__main__":
    unittest.main()
