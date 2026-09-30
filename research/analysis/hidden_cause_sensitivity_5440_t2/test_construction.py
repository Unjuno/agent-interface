import json
import unittest
from pathlib import Path

import audit
import candidate


ROOT = Path(__file__).parent
DATA = json.loads((ROOT / "cases.json").read_bytes())


class ConstructionTests(unittest.TestCase):
    def test_unverified_family_fails_closed_despite_declared_robustness(self):
        pair = DATA["pairs"][0]
        self.assertGreater(
            candidate.q(pair["nominal"]) - candidate.q(pair["declared_risk"]), 0
        )
        self.assertEqual(candidate.decide(pair, DATA, "unverified_family")["decision"], "UNIDENTIFIED")

    def test_valid_complete_scope_allows_only_declared_model_decision(self):
        pair = DATA["pairs"][0]
        self.assertEqual(candidate.decide(pair, DATA, "attested_complete")["decision"], "ROBUST")

    def test_scope_and_issuer_corruption_fail_closed(self):
        pair = DATA["pairs"][0]
        for mode in DATA["candidate_controls"]:
            with self.subTest(mode=mode):
                self.assertEqual(candidate.decide(pair, DATA, mode)["decision"], "UNIDENTIFIED")

    def test_raw_only_oracle_constructs_eight_hidden_reversals(self):
        rows = audit.expected(DATA)
        truths = rows[:16]
        hidden = [truths[i] for i in range(1, len(truths), 2)]
        complete = [truths[i] for i in range(0, len(truths), 2)]
        self.assertEqual(sum(row["audit_only_truth"]["reversal"] for row in hidden), 8)
        self.assertEqual(sum(row["audit_only_truth"]["reversal"] for row in complete), 0)
        self.assertEqual(sum(row["decision"] == "UNIDENTIFIED" for row in hidden), 8)


if __name__ == "__main__":
    unittest.main(verbosity=2)
