import copy
import json
import unittest
from pathlib import Path

from effect_oracle import apply, audit

ROOT = Path(__file__).parent
CASES = json.loads((ROOT.parent / "issue4680-skillpackage-construction" / "cases.json").read_text())["cases"]
RESULT = json.loads((ROOT.parent / "issue4680-skillpackage-construction" / "outputs" / "formal01" / "result.json").read_text())


class IndependentOracleTests(unittest.TestCase):
    def test_retained_formal_rows_match_independent_transitions(self):
        report = audit(CASES, RESULT)
        self.assertEqual(report["decision"], "PASS_EFFECT_ORACLE_SCOPED", report["errors"])
        self.assertEqual(report["rows_checked"], 10)

    def test_toggle_computes_persisted_boolean_effect(self):
        case = next(c for c in CASES if c["id"] == "nominal_toggle")
        row = next(r for r in RESULT["rows"] if r["id"] == case["id"])
        state, effect = apply(row["proposal"], case)
        self.assertTrue(state["values"]["email_reminders"])
        self.assertEqual(effect, {"email_reminders": True})

    def test_field_action_is_staged_not_persisted(self):
        case = next(c for c in CASES if c["id"] == "local_correction")
        row = next(r for r in RESULT["rows"] if r["id"] == case["id"])
        state, effect = apply(row["proposal"], case)
        self.assertEqual(state["staged"]["digest_frequency"], "monthly")
        self.assertEqual(state["values"]["digest_frequency"], "daily")
        self.assertEqual(effect, {})

    def test_multistep_save_commits_staged_value(self):
        case = next(c for c in CASES if c["id"] == "multistep_save")
        row = next(r for r in RESULT["rows"] if r["id"] == case["id"])
        state, effect = apply(row["proposal"], case)
        self.assertEqual(state["values"]["digest_frequency"], "weekly")
        self.assertEqual(state["staged"], {})
        self.assertEqual(effect, {"digest_frequency": "weekly", "saved": True})

    def test_expected_effect_tampering_is_detected(self):
        cases = copy.deepcopy(CASES)
        result = copy.deepcopy(RESULT)
        next(c for c in cases if c["id"] == "nominal_toggle")["effect"]["email_reminders"] = False
        self.assertIn("INDEPENDENT_EFFECT_MISMATCH:nominal_toggle", audit(cases, result)["errors"])

    def test_proposal_tampering_is_detected_even_if_claimed_effect_matches(self):
        result = copy.deepcopy(RESULT)
        row = next(r for r in result["rows"] if r["id"] == "nominal_toggle")
        row["proposal"]["arguments"]["target"] = "delete_workspace"
        report = audit(CASES, result)
        self.assertTrue(any("PROPOSAL_MISMATCH:nominal_toggle" == e for e in report["errors"]))
        self.assertTrue(any(e.startswith("TRANSITION_REJECTED:nominal_toggle:") for e in report["errors"]))

    def test_missing_row_is_detected(self):
        result = copy.deepcopy(RESULT)
        result["rows"].pop()
        self.assertIn("ROW_CARDINALITY_OR_DUPLICATE", audit(CASES, result)["errors"])
        self.assertIn("ROW_CASE_SET", audit(CASES, result)["errors"])

    def test_save_without_stage_refuses(self):
        case = next(c for c in CASES if c["id"] == "multistep_save")
        broken = copy.deepcopy(case)
        broken["state"]["staged"] = {}
        row = next(r for r in RESULT["rows"] if r["id"] == case["id"])
        with self.assertRaisesRegex(ValueError, "SAVE_WITHOUT_STAGED_VALUE"):
            apply(row["proposal"], broken)


if __name__ == "__main__":
    unittest.main(verbosity=2)

