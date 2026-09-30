import copy
import json
import unittest
from pathlib import Path

from effect_oracle import apply, audit

ROOT = Path(__file__).parent
CASES = json.loads((ROOT.parent / "issue4680-skillpackage-construction" / "cases.json").read_text())["cases"]
RESULT = json.loads((ROOT.parent / "issue4680-skillpackage-construction" / "outputs" / "formal01" / "result.json").read_text())


class PostconditionOracleTests(unittest.TestCase):
    def test_retained_rows_pass_independent_postcondition_audit(self):
        report = audit(CASES, RESULT)
        self.assertEqual(report["decision"], "PASS_POSTCONDITION_ORACLE_SCOPED", report["errors"])
        self.assertEqual(report["rows_checked"], 10)

    def test_no_action_derives_satisfied_state_without_reading_effect_label(self):
        case = copy.deepcopy(next(c for c in CASES if c["id"] == "already_satisfied"))
        case["effect"] = {"email_reminders": False}
        row = next(r for r in RESULT["rows"] if r["id"] == case["id"])
        _, postcondition = apply(row["proposal"], case)
        self.assertEqual(postcondition, {"email_reminders": True})

    def test_field_stages_but_does_not_persist(self):
        case = next(c for c in CASES if c["id"] == "local_correction")
        row = next(r for r in RESULT["rows"] if r["id"] == case["id"])
        state, postcondition = apply(row["proposal"], case)
        self.assertEqual(state["staged"]["digest_frequency"], "monthly")
        self.assertEqual(state["values"]["digest_frequency"], "daily")
        self.assertEqual(postcondition, {})

    def test_save_commits_one_staged_supported_field(self):
        case = next(c for c in CASES if c["id"] == "multistep_save")
        row = next(r for r in RESULT["rows"] if r["id"] == case["id"])
        state, postcondition = apply(row["proposal"], case)
        self.assertEqual(state["values"]["digest_frequency"], "weekly")
        self.assertEqual(state["staged"], {})
        self.assertEqual(postcondition, {"digest_frequency": "weekly", "saved": True})

    def test_toggle_is_recomputed_from_initial_state(self):
        case = next(c for c in CASES if c["id"] == "nominal_toggle")
        row = next(r for r in RESULT["rows"] if r["id"] == case["id"])
        state, postcondition = apply(row["proposal"], case)
        self.assertTrue(state["values"]["email_reminders"])
        self.assertEqual(postcondition, {"email_reminders": True})

    def test_wrong_expected_label_is_detected(self):
        cases = copy.deepcopy(CASES)
        next(c for c in cases if c["id"] == "nominal_toggle")["effect"]["email_reminders"] = False
        self.assertIn("INDEPENDENT_POSTCONDITION_MISMATCH:nominal_toggle", audit(cases, RESULT)["errors"])

    def test_wrong_target_is_rejected(self):
        result = copy.deepcopy(RESULT)
        next(r for r in result["rows"] if r["id"] == "nominal_toggle")["proposal"]["arguments"]["target"] = "delete_workspace"
        report = audit(CASES, result)
        self.assertIn("PROPOSAL_MISMATCH:nominal_toggle", report["errors"])
        self.assertTrue(any(e.startswith("TRANSITION_REJECTED:nominal_toggle:") for e in report["errors"]))

    def test_missing_row_is_rejected(self):
        result = copy.deepcopy(RESULT)
        result["rows"].pop()
        report = audit(CASES, result)
        self.assertIn("ROW_CARDINALITY_OR_DUPLICATE", report["errors"])
        self.assertIn("ROW_CASE_SET", report["errors"])

    def test_broken_multistep_link_is_rejected(self):
        result = copy.deepcopy(RESULT)
        next(r for r in result["rows"] if r["id"] == "multistep_save")["prior_step_ok"] = False
        self.assertIn("MULTISTEP_LINK_INVALID", audit(CASES, result)["errors"])


if __name__ == "__main__":
    unittest.main(verbosity=2)

