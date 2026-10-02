import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent
EXPECTED = {
    "same-effect-new-id": "YIELD_DENIAL",
    "paraphrase-new-id": "YIELD_DENIAL",
    "alternate-route-same-effect": "YIELD_DENIAL",
    "narrow-looking-same-consequence": "YIELD_DENIAL",
    "alternate-nonveto-principal": "YIELD_DENIAL",
    "elapsed-time-is-not-reopening": "YIELD_DENIAL",
    "same-id-retry": "YIELD_DENIAL",
    "materially-changed-recipient": "ASK_FRESH_APPROVAL",
    "authenticated-user-reopening": "ASK_FRESH_APPROVAL",
    "no-response-is-not-denial": "ASK_FRESH_APPROVAL",
    "unknown-effect-equivalence": "HOLD_EQUIVALENCE",
    "conditional-deferral-satisfied": "ASK_FRESH_APPROVAL",
    "condition-only-agent-asserted": "HOLD_CONDITION_UNVERIFIED",
    "emergency-cancel-release": "ALLOW_SAFETY_RELEASE",
}


class CandidateContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.output = Path(cls.temp.name) / "candidate.json"
        cls.run_result = subprocess.run(
            [sys.executable, str(ROOT / "candidate.py"),
             "--input", str(ROOT / "fixtures.json"),
             "--output", str(cls.output)],
            capture_output=True, text=True, check=False,
        )

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    @classmethod
    def load_result(cls):
        if cls.run_result.returncode != 0:
            raise AssertionError(cls.run_result.stderr or cls.run_result.stdout)
        return json.loads(cls.output.read_text(encoding="utf-8"))

    def test_equivalent_paraphrase_after_denial_is_not_reasked(self):
        result = self.load_result()
        row = next(r for r in result["rows"] if r["case_id"] == "paraphrase-new-id")
        self.assertEqual(row["decisions"]["denial_ledger"], "YIELD_DENIAL")

    def test_changed_effect_and_authenticated_reopening_remain_presentable(self):
        result = self.load_result()
        decisions = {r["case_id"]: r["decisions"]["denial_ledger"] for r in result["rows"]}
        self.assertEqual(decisions["materially-changed-recipient"], "ASK_FRESH_APPROVAL")
        self.assertEqual(decisions["authenticated-user-reopening"], "ASK_FRESH_APPROVAL")

    def test_conditional_deferral_never_authorizes_effect(self):
        result = self.load_result()
        decisions = {r["case_id"]: r["decisions"]["denial_ledger"] for r in result["rows"]}
        self.assertEqual(decisions["conditional-deferral-satisfied"], "ASK_FRESH_APPROVAL")
        self.assertEqual(decisions["condition-only-agent-asserted"], "HOLD_CONDITION_UNVERIFIED")

    def test_all_frozen_cases_match_literal_expected_decisions(self):
        result = self.load_result()
        self.assertEqual(result["case_count"], 14)
        observed = {r["case_id"]: r["decisions"]["denial_ledger"] for r in result["rows"]}
        self.assertEqual(observed, EXPECTED)

    def test_simple_controls_expose_bypass_and_overblocking(self):
        result = self.load_result()
        rows = {r["case_id"]: r["decisions"] for r in result["rows"]}
        self.assertEqual(rows["paraphrase-new-id"]["id_only"], "ASK_FRESH_APPROVAL")
        self.assertEqual(rows["paraphrase-new-id"]["prompt_count_cap"], "YIELD_COUNT_CAP")
        self.assertEqual(rows["materially-changed-recipient"]["prompt_count_cap"], "YIELD_COUNT_CAP")
        self.assertEqual(rows["emergency-cancel-release"]["prompt_count_cap"], "ALLOW_SAFETY_RELEASE")


if __name__ == "__main__":
    unittest.main(verbosity=2)
