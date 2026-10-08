"""Pre-freeze construction tests; they do not invoke candidate/auditor CLIs."""
import copy
import unittest

import auditor
import candidate


class TraceFixtureTests(unittest.TestCase):
    def test_valid_fixture(self):
        self.assertEqual(auditor.audit(candidate.build_records()), [])

    def test_wrong_task_effect_rejected(self):
        raw = copy.deepcopy(candidate.build_records())
        next(r for r in raw["episodes"] if r["id"] == "pre_decision" and r["arm"] == "omission")["task_effect"] = "wrong"
        self.assertTrue(auditor.audit(raw))

    def test_wrong_visibility_cost_rejected(self):
        raw = copy.deepcopy(candidate.build_records())
        next(r for r in raw["episodes"] if r["id"] == "post_completion" and r["arm"] == "omission")["visible_bytes"] = 400
        self.assertTrue(auditor.audit(raw))

    def test_capture_delivery_collapse_rejected(self):
        raw = copy.deepcopy(candidate.build_records())
        row = next(r for r in raw["episodes"] if r["id"] == "captured_undelivered")
        row["captured"] = 0
        self.assertTrue(auditor.audit(raw))

    def test_mandatory_safety_omission_rejected(self):
        raw = copy.deepcopy(candidate.build_records())
        row = next(r for r in raw["episodes"] if r["id"] == "mandatory_safety")
        row["mandatory_cue_delivered"] = False
        self.assertTrue(auditor.audit(raw))

    def test_stop_outcome_mutation_rejected(self):
        raw = copy.deepcopy(candidate.build_records())
        next(r for r in raw["episodes"] if r["id"] == "cross_transition" and r["arm"] == "omission")["stop_outcome"] = "completed_exactly"
        self.assertTrue(auditor.audit(raw))

    def test_decision_trace_mutation_rejected(self):
        raw = copy.deepcopy(candidate.build_records())
        next(r for r in raw["episodes"] if r["id"] == "pre_decision" and r["arm"] == "omission")["decision"] = "act_on_stale_A"
        self.assertTrue(auditor.audit(raw))

    def test_interval_state_mutation_rejected(self):
        raw = copy.deepcopy(candidate.build_records())
        next(r for r in raw["episodes"] if r["id"] == "cross_transition" and r["arm"] == "omission")["state"] = "after_completion"
        self.assertTrue(auditor.audit(raw))


if __name__ == "__main__":
    unittest.main()
