import json
import unittest
from pathlib import Path

import auditor
import candidate

HERE = Path(__file__).resolve().parent
FIXTURE = json.loads((HERE / "fixture.json").read_text())


class HomologyHomotopyTests(unittest.TestCase):
    def setUp(self):
        self.raw = candidate.analyze(FIXTURE)

    def test_two_obstacle_geometry_emits_ordered_commutator(self):
        row = next(r for r in self.raw["rows"] if r["word"] == "abAB")
        self.assertEqual((row["crossing_word"], row["homology"], row["reduced"]), ("abAB", [0, 0], "abAB"))

    def test_identity_and_commutator_collide_in_homology_not_homotopy(self):
        result = auditor.audit(self.raw, FIXTURE)
        self.assertEqual(result["audit_status"], "PASS")
        control = next(c for c in self.raw["controls"] if c["id"] == "commutator_collision")
        self.assertTrue(control["homology_equal"])
        self.assertFalse(control["homotopy_equal"])

    def test_adjacent_inverse_and_equal_word_different_length_controls(self):
        result = {c["id"]: c for c in self.raw["controls"]}
        self.assertTrue(result["adjacent_inverse_cancellation"]["homotopy_equal"])
        self.assertTrue(result["same_word_different_route_length"]["homotopy_equal"])

    def test_one_obstacle_abelianization_has_no_bounded_collision(self):
        self.assertEqual(self.raw["one_obstacle_summary"]["homology_buckets_with_multiple_homotopy_words"], 0)

    def test_incomplete_missing_and_stale_evidence_is_unknown(self):
        controls = {c["id"]: c for c in self.raw["controls"]}
        for key in ("unfinished_prefix", "missing_crossing_receipt", "geometry_revision"):
            self.assertEqual(controls[key]["decision"], "UNKNOWN")

    def test_mutations_are_rejected(self):
        mutations = []
        m = json.loads(json.dumps(self.raw)); next(r for r in m["rows"] if r["word"] == "abAB")["homology"] = [1, 0]; mutations.append(m)
        m = json.loads(json.dumps(self.raw)); next(r for r in m["rows"] if r["word"] == "abAB")["crossing_word"] = ""; mutations.append(m)
        m = json.loads(json.dumps(self.raw)); next(c for c in m["controls"] if c["id"] == "commutator_collision")["homotopy_equal"] = True; mutations.append(m)
        m = json.loads(json.dumps(self.raw)); m["rows"].pop(); mutations.append(m)
        m = json.loads(json.dumps(self.raw)); next(c for c in m["controls"] if c["id"] == "geometry_revision")["decision"] = "COMPARE"; mutations.append(m)
        for mutant in mutations:
            self.assertNotEqual(auditor.audit(mutant, FIXTURE)["audit_status"], "PASS")

    def test_all_raw_route_words_have_complete_receipts(self):
        self.assertEqual(len(self.raw["rows"]), 5461)
        self.assertTrue(all(row["complete"] for row in self.raw["rows"]))


if __name__ == "__main__":
    unittest.main()
