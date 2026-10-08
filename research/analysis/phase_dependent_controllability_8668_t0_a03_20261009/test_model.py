"""Construction tests for the Issue #8668 A03 finite schedule contract."""
import json
import copy
import unittest
from pathlib import Path

import candidate
import auditor


class ScheduleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.design = json.loads((Path(__file__).parent / "design.json").read_text())
        cls.rows = candidate.schedules(cls.design)

    def test_schedule_product_is_unique_and_includes_control(self):
        ids = [json.dumps(row, sort_keys=True) for row in self.rows]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(self.rows[-1]["timeline"], "no_input_control")
        self.assertGreater(len(self.rows), 100)
        self.assertEqual(self.rows, auditor.expected_schedules(self.design))

    def test_frozen_mutation_controls_are_all_applicable(self):
        expected = auditor.expected_schedules(self.design)
        controls = auditor.mutation_controls(expected, self.design)
        self.assertEqual(len(controls), 9)
        self.assertEqual(len({name for name, _ in controls}), 9)
        synthetic = {"rows": [
            {"exogenous": row, "strict": auditor.oracle(row, self.design, identity=True)}
            for row in expected
        ]}
        for name, mutate in controls:
            with self.subTest(control=name):
                changed = copy.deepcopy(synthetic)
                self.assertTrue(mutate(changed))
                self.assertFalse(auditor.audit_without_mutations(changed, expected, self.design))

    def test_stale_effect_does_not_confirm_active_attempt(self):
        row = next(x for x in self.rows if x["timeline"] == "stale_effect" and x["phase"] == "EMITTED" and x["effect_committed"])
        result = candidate.decide(row, self.design, bind_identity=True)
        self.assertEqual(result["status"], "UNKNOWN")
        self.assertFalse(result["retry_admitted"])

    def test_same_operation_id_still_requires_matching_attempt(self):
        for timeline in ("same_id_stale_effect", "same_id_stale_then_current_effect", "current_effect_then_same_id_stale"):
            row = next(x for x in self.rows if x["timeline"] == timeline and x["phase"] == "EMITTED" and x["effect_committed"])
            self.assertEqual(row["receipts"][0]["operation_id"], self.design["active_operation_id"])
            self.assertEqual(len({ack["attempt"] for ack in row["receipts"]}), 2 if len(row["receipts"]) == 2 else 1)
            strict = candidate.decide(row, self.design, bind_identity=True)
            if timeline == "same_id_stale_effect":
                self.assertEqual(strict["status"], "UNKNOWN")
                self.assertEqual(strict["accepted_ack_ids"], [])
            else:
                self.assertEqual(strict["status"], "COMPLETED")
                self.assertEqual(strict["accepted_ack_ids"], [f"ack-{self.design['active_operation_id']}-attempt-{self.design['active_attempt']}-EFFECT_CONFIRMED-1"])

    def test_same_id_stale_cancel_does_not_authorize_retry(self):
        row = next(x for x in self.rows if x["timeline"] == "same_id_stale_cancel" and x["phase"] == "QUEUED" and x["retry_requested"])
        strict = candidate.decide(row, self.design, bind_identity=True)
        identity_blind = candidate.decide(row, self.design, bind_identity=False)
        self.assertEqual(strict["status"], "PENDING")
        self.assertFalse(strict["retry_admitted"])
        self.assertEqual(identity_blind["status"], "CANCELLED_BEFORE_EMIT")
        self.assertTrue(identity_blind["retry_admitted"])

    def test_stale_cancel_does_not_authorize_retry(self):
        row = next(x for x in self.rows if x["timeline"] == "stale_cancel" and x["phase"] == "QUEUED" and x["retry_requested"])
        result = candidate.decide(row, self.design, bind_identity=True)
        faulty = candidate.decide(row, self.design, bind_identity=False)
        self.assertEqual(result["status"], "PENDING")
        self.assertFalse(result["retry_admitted"])
        self.assertEqual(faulty["status"], "CANCELLED_BEFORE_EMIT")
        self.assertTrue(faulty["retry_admitted"])

    def test_exact_active_receipts_preserve_safe_decisions(self):
        confirmed = next(x for x in self.rows if x["timeline"] == "current_effect" and x["phase"] == "EMITTED" and x["effect_committed"])
        cancelled = next(x for x in self.rows if x["timeline"] == "current_cancel" and x["phase"] == "QUEUED" and x["retry_requested"])
        self.assertEqual(candidate.decide(confirmed, self.design, bind_identity=True)["status"], "COMPLETED")
        self.assertTrue(candidate.decide(cancelled, self.design, bind_identity=True)["retry_admitted"])

    def test_replayed_active_ack_is_idempotent(self):
        row = next(x for x in self.rows if x["timeline"] == "current_effect_replayed" and x["phase"] == "EMITTED" and x["effect_committed"])
        result = candidate.decide(row, self.design, bind_identity=True)
        self.assertEqual(result["status"], "COMPLETED")
        self.assertEqual(len(result["accepted_ack_ids"]), 1)

    def test_contradictory_active_ack_order_fails_closed(self):
        for timeline in ("current_effect_then_current_cancel", "current_cancel_then_current_effect"):
            row = next(x for x in self.rows if x["timeline"] == timeline and x["phase"] == "EMITTED" and x["effect_committed"] and x["retry_requested"])
            result = candidate.decide(row, self.design, bind_identity=True)
            self.assertEqual(result["status"], "CONFLICT_UNKNOWN")
            self.assertFalse(result["retry_admitted"])
            self.assertEqual(result["accepted_ack_ids"], [])

    def test_late_active_cancel_ack_after_emit_does_not_authorize_retry(self):
        row = next(x for x in self.rows if x["timeline"] == "current_cancel" and x["phase"] == "EMITTED" and x["retry_requested"])
        result = candidate.decide(row, self.design, bind_identity=True)
        self.assertEqual(result["status"], "UNKNOWN")
        self.assertFalse(result["retry_admitted"])

    def test_neutral_release_is_not_semantic_cancellation(self):
        row = next(x for x in self.rows if x["timeline"] == "none" and x["phase"] == "QUEUED" and x["retry_requested"] and x["neutral_release_observed"])
        result = candidate.decide(row, self.design, bind_identity=True)
        self.assertEqual(result["status"], "PENDING")
        self.assertFalse(result["retry_admitted"])

    def test_post_emit_without_active_receipt_remains_unknown(self):
        row = next(x for x in self.rows if x["timeline"] == "none" and x["phase"] == "CONSUMED" and x["retry_requested"])
        result = candidate.decide(row, self.design, bind_identity=True)
        self.assertEqual(result["status"], "UNKNOWN")
        self.assertFalse(result["retry_admitted"])


if __name__ == "__main__":
    unittest.main()
