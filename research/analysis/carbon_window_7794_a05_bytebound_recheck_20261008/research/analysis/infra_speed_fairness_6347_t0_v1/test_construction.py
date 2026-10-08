import json
import unittest
from pathlib import Path

import candidate
import audit


ROOT = Path(__file__).parent


class FairnessConstructionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = json.loads((ROOT / "fixture.json").read_text())
        cls.raw = candidate.run(cls.fixture)
        cls.audit = audit.audit(cls.fixture, cls.raw)

    def test_independent_reconstruction_and_mutations(self):
        self.assertTrue(self.audit["pass"])
        self.assertEqual(self.audit["reconstructed_rows"], len(self.raw["rows"]))
        self.assertTrue(self.audit["all_mutations_rejected"])
        self.assertEqual(self.audit["mutation_rejections"], [True] * 4)

    def test_delay_swap_changes_frfs_but_not_batch_in_planted_ties(self):
        rows = [r for r in self.raw["rows"] if r["case"].startswith("paired-fast-")]
        winners = {(r["policy"], r["arm"]): r["winner"] for r in rows}
        self.assertNotEqual(winners[("frfs", "baseline")], winners[("frfs", "delay_swapped")])
        self.assertEqual(winners[("batch_rotate", "baseline")], winners[("batch_rotate", "delay_swapped")])

    def test_hard_safety_gates_and_no_rights_hold(self):
        rows = {(r["case"], r["policy"]): r for r in self.raw["rows"] if r["phase"] == "safety"}
        self.assertTrue(all(rows[("rights-unresolved", p)]["status"] == "HOLD_NO_TIE_RIGHTS" for p in candidate.POLICIES))
        self.assertEqual(rows[("revoked-during-window", "batch_rotate")]["status"], "REFUSE_REVOKED")
        self.assertEqual(rows[("expired-evidence", "batch_rotate")]["status"], "REFUSE_STALE")
        self.assertEqual(rows[("disjoint-negative-control", "batch_rotate")]["status"], "ADMITTED_DISJOINT")

    def test_repeated_equal_rights_rotation_is_bounded(self):
        wins = [r["winner"] for r in self.raw["rows"] if r["case"] == "repeated-tie-rotation" and r["policy"] == "batch_rotate"]
        self.assertEqual(wins, ["A", "B", "A", "B", "A", "B"])


if __name__ == "__main__":
    unittest.main()
