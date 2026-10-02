import copy
import json
import unittest
from pathlib import Path

from candidate import summarize
from independent_audit import audit


HERE = Path(__file__).resolve().parent


class IndependentAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = json.loads((HERE / "fixture.json").read_text(encoding="utf-8"))
        cls.candidate = summarize(cls.fixture["episodes"], cls.fixture["horizons_from_launch"])

    def test_independently_reconstructs_all_rows_and_denominators(self):
        result = audit(self.fixture, self.candidate)
        self.assertEqual(result["status"], "PASS_METHOD_SCOPED")
        self.assertEqual(result["reconstructed_episodes"], 5)
        self.assertEqual(result["reconstructed_horizon_rows"], 10)

    def test_rejects_missing_launched_episode(self):
        mutated = copy.deepcopy(self.fixture)
        mutated["episodes"].pop()
        result = audit(mutated, self.candidate)
        self.assertEqual(result["status"], "FAIL_METHOD_SCOPED")

    def test_rejects_false_clean_success_after_followup_loss(self):
        mutated = copy.deepcopy(self.candidate)
        row = next(x for x in mutated["episodes"] if x["episode_id"] == "followup-lost")
        row["horizons"]["6"]["status"] = "NO_COLLATERAL_COMPLETE"
        self.assertEqual(audit(self.fixture, mutated)["status"], "FAIL_METHOD_SCOPED")

    def test_rejects_relabeling_late_collateral_as_first_terminal_failure(self):
        mutated = copy.deepcopy(self.candidate)
        mutated["first_terminal_counts"]["verified_success"] -= 1
        mutated["first_terminal_counts"]["verified_failure"] += 1
        self.assertEqual(audit(self.fixture, mutated)["status"], "FAIL_METHOD_SCOPED")


if __name__ == "__main__":
    unittest.main()
