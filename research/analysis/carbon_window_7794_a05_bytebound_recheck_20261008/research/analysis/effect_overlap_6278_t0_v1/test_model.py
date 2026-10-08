import json
import unittest
from pathlib import Path

import audit
import candidate


ROOT = Path(__file__).parent


class EligibilityTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = json.loads((ROOT / "fixture.json").read_text())
        cls.raw = candidate.run(cls.fixture)

    def row(self, task):
        return next(r for r in self.raw["rows"] if r["task"] == task)

    def test_nominal_exact_effects_complete(self):
        self.assertEqual([self.row(f"n{i}")["status"] for i in (1, 2, 3)], ["EXACT_ON_TIME"] * 3)

    def test_shared_dependency_loss_blocks_shared_routes(self):
        self.assertEqual(self.row("s1")["status"], "ABSTAIN")
        self.assertEqual(self.row("s2")["status"], "ABSTAIN")

    def test_reconfiguration_after_deadline_is_not_buffering(self):
        self.assertEqual(self.row("l1")["status"], "ABSTAIN")

    def test_partial_and_unauthorized_edges_never_count(self):
        self.assertEqual(self.row("p1")["status"], "ABSTAIN")
        self.assertEqual(self.row("p2")["status"], "ABSTAIN")

    def test_independent_oracle_agrees_on_every_row(self):
        self.assertEqual(audit.audit(self.fixture, self.raw)["disposition"], "PASS_METHOD_SCOPED")

    def test_mutations_rejected(self):
        for mutate in (
            lambda rows: rows[0].update(route="specialist_c"),
            lambda rows: rows[3].update(status="EXACT_ON_TIME", route="overlap_ab", completion_ms=11),
            lambda rows: rows.pop(),
            lambda rows: rows.append(dict(rows[0])),
        ):
            corrupted = json.loads(json.dumps(self.raw))
            mutate(corrupted["rows"])
            self.assertEqual(audit.audit(self.fixture, corrupted)["disposition"], "FAIL_AUDIT_GATE")


if __name__ == "__main__":
    unittest.main()
