import itertools
import unittest

import audit
import model


class RestartConvergenceTests(unittest.TestCase):
    def test_full_product_size_is_frozen(self):
        self.assertEqual(sum(1 for _ in model.configurations()), 13824)

    def test_all_fair_local_step_orders(self):
        state = next(model.configurations())
        original_epochs = list(state["epochs"])
        schedules = list(itertools.permutations(model.STEPS))
        self.assertEqual(len(schedules), 120)
        outcomes = [model.play_fair_schedule(state, order) for order in schedules]
        self.assertTrue(all(result["admissions"] == 0 for result in outcomes))
        self.assertEqual(state["epochs"], original_epochs)

    def test_unavailable_release_never_claims_quiescence(self):
        state = next(s for s in model.configurations() if not s["release_oracle"])
        for order in itertools.permutations(model.STEPS):
            self.assertEqual(model.play_fair_schedule(state, order)["destination"], "HOLD_UNKNOWN_INPUT")

    def test_resume_requires_release_effect_target_and_new_authority(self):
        base = next(s for s in model.configurations() if s["release_oracle"] and s["effect_oracle"] and s["effect"] == "NONE" and s["target_state"] == "CURRENT" and s["new_authorization"] and s["pending_claim"])
        outcome = model.play_fair_schedule(base, model.STEPS)
        self.assertEqual(outcome["destination"], "RESUMABLE_CURRENT")
        for key, value in (("effect_oracle", False), ("target_state", "STALE"), ("new_authorization", False), ("release_oracle", False)):
            changed = {**base, key: value}
            self.assertNotEqual(model.play_fair_schedule(changed, model.STEPS)["destination"], "RESUMABLE_CURRENT")

    def test_naive_restore_has_a_counterexample_and_stop_has_no_progress(self):
        self.assertTrue(any(model.naive_violation(s) for s in model.configurations()))
        self.assertFalse(any(row["permanent_stop_progress"] for row in model.candidate_rows()))

    def test_old_duplicate_messages_cannot_reopen_gate(self):
        self.assertEqual(len(model.message_permutations()), 12)
        for order in model.message_permutations():
            self.assertEqual(model.message_gate_result(order), (0, 0))

    def test_raw_only_auditor_rejects_mutated_result_or_missing_state(self):
        rows = list(model.candidate_rows())
        self.assertEqual(audit.audit_records(rows)["status"], "METHOD_PASS_SCOPED")
        changed = [dict(row) for row in rows]
        changed[0]["destination"] = "RESUMABLE_CURRENT"
        self.assertEqual(audit.audit_records(changed)["status"], "FAIL_METHOD")
        bool_substitution = [dict(row) for row in rows]
        bool_substitution[0] = {**rows[0], "state_id": False}
        self.assertEqual(audit.audit_records(bool_substitution)["errors"], ["state_inventory:0"])
        self.assertEqual(audit.audit_records(rows[:-1])["errors"], ["state_count"])
        self.assertEqual(audit.audit_records(["not an object"])["errors"], ["raw_record_shape"])


if __name__ == "__main__":
    unittest.main()
