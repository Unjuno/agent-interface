import copy
import json
import unittest
from pathlib import Path

import audit
import candidate


DATA = json.loads(Path(__file__).with_name("fixtures.json").read_text(encoding="utf-8"))


class ConstructionTests(unittest.TestCase):
    def test_eight_frozen_cases(self):
        self.assertEqual(len(DATA["cases"]), 8)
        self.assertEqual(len({c["case_id"] for c in DATA["cases"]}), 8)
        self.assertEqual(DATA["allocation_id"], "CROSS-TASK-SUCCESS-HISTORY-CALIBRATION-6241-T0-20261002-01")

    def test_identical_success_streak_only_transfers_with_declared_relation(self):
        rows = candidate.build(DATA)["rows"]
        self.assertEqual(rows[0]["transferred_success_probability"], 0.75)
        self.assertEqual(rows[1]["transferred_success_probability"], 0.5)
        self.assertEqual(rows[0]["decision"], "PROPOSE_ROUTE")
        self.assertEqual(rows[1]["decision"], "VERIFY_CURRENT_B")

    def test_changed_precondition_and_capability_mismatch_do_not_transfer(self):
        rows = candidate.build(DATA)["rows"]
        self.assertFalse(rows[2]["transfer_eligible"])
        self.assertFalse(rows[7]["transfer_eligible"])

    def test_weak_same_regime_history_is_calibrated_below_threshold(self):
        row = candidate.build(DATA)["rows"][3]
        self.assertEqual(row["transferred_success_probability"], 0.25)
        self.assertEqual(row["decision"], "VERIFY_CURRENT_B")

    def test_unknown_and_ambiguous_states_fail_closed(self):
        rows = candidate.build(DATA)["rows"]
        self.assertEqual(rows[4]["decision"], "HOLD_AMBIGUOUS_EFFECT")
        self.assertEqual(rows[5]["decision"], "HOLD_UNKNOWN_DEPENDENCY")
        self.assertEqual(rows[4]["open_obligations"], ["obligation-A-effect-77"])

    def test_private_history_not_included_in_capsule(self):
        row = candidate.build(DATA)["rows"][6]
        self.assertEqual(row["included_history_artifact_ids"], [])
        self.assertNotIn("A-only note", json.dumps(row))

    def test_independent_auditor_reconstructs_candidate_and_mutations(self):
        raw = candidate.build(DATA)
        self.assertTrue(audit.verify(DATA, raw))
        self.assertEqual(sum(audit.mutations(DATA, raw).values()), 6)

    def test_current_b_identity_is_preserved_for_every_case(self):
        rows = candidate.build(DATA)["rows"]
        self.assertTrue(all(r["current_b"] == DATA["current_b"] for r in rows))


if __name__ == "__main__":
    unittest.main(verbosity=2)
