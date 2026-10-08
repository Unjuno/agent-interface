import json
import unittest
from pathlib import Path

import candidate
import audit


ROOT = Path(__file__).parent


class BoundaryConstructionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = json.loads((ROOT / "fixture.json").read_text())
        cls.raw = candidate.run(cls.fixture)
        cls.audit = audit.audit(cls.fixture, cls.raw)

    def test_independent_exact_reconstruction_and_mutations(self):
        self.assertTrue(self.audit["pass"])
        self.assertEqual(self.audit["reconstructed_rows"], 16)
        self.assertEqual(self.audit["mutation_rejections"], [True] * 4)

    def test_phase_jitter_changes_membership_and_winner(self):
        rows = {r["case"]: r for r in self.raw["rows"] if r["pair"] == "phase-jitter"}
        self.assertEqual(rows["phase-before-close"]["collected"], ["A", "B"])
        self.assertEqual(rows["phase-before-close"]["batch_winner"], "B")
        self.assertEqual(rows["phase-after-close"]["collected"], ["A"])
        self.assertEqual(rows["phase-after-close"]["deferred"], ["B"])
        self.assertEqual(rows["phase-after-close"]["batch_winner"], "A")

    def test_deliberate_send_delay_crosses_close(self):
        rows = {r["case"]: r for r in self.raw["rows"] if r["pair"] == "strategic-send"}
        self.assertEqual(rows["strategic-submit-before-close"]["batch_winner"], "B")
        self.assertEqual(rows["strategic-submit-after-close"]["batch_winner"], "A")
        self.assertEqual(rows["strategic-submit-after-close"]["deferred"], ["B"])

    def test_all_repeated_windows_and_pointer_transitions_retained(self):
        rows = [r for r in self.raw["rows"] if r["pair"] == "multi-window"]
        self.assertEqual(len(rows), 12)
        self.assertEqual([r["batch_winner"] for r in rows], ["B", "A"] * 6)
        self.assertEqual([r["pointer_before"] for r in rows[1:]], [r["pointer_after"] for r in rows[:-1]])


if __name__ == "__main__":
    unittest.main()
