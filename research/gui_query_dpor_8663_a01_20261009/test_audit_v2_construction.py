"""Pre-freeze checks for the separate audit-v2 prefix replay implementation."""
import json
import unittest
from pathlib import Path

import audit_v2
import candidate

ROOT = Path(__file__).resolve().parent
MODEL = json.loads((ROOT / "MODEL.json").read_text())


class AuditV2ConstructionTests(unittest.TestCase):
    def test_audit_source_does_not_import_candidate(self):
        source = (ROOT / "audit_v2.py").read_text()
        self.assertNotIn("import candidate", source)
        self.assertNotIn("from candidate", source)

    def test_prefix_replay_accepts_legal_prefix_and_rejects_bad_order(self):
        case = next(c for c in MODEL["cases"] if c["id"] == "matching_insert")
        state = audit_v2.replay_prefix(case, ["a-insert", "query"])
        self.assertEqual(state["query"]["members"], ["A", "B"])
        with self.assertRaisesRegex(ValueError, "prerequisites"):
            audit_v2.replay_prefix(case, ["validate"])

    def test_full_and_reduced_history_sets_match_candidate_construction(self):
        for case in MODEL["cases"]:
            self.assertEqual(
                {tuple(row["schedule"]) for row in candidate.exhaustive(case)},
                {tuple(row["schedule"]) for row in audit_v2.all_orders(case)}, case["id"])
            for c_mode, a_mode in (("predicate", "predicate"),
                                   ("node_only", "node_only"),
                                   ("mutant_cross_scope", "mutant_cross_scope"),
                                   ("mutant_unknown_independent", "mutant_unknown_independent")):
                c_rows, _ = candidate.sleep_set(case, c_mode)
                a_rows, _ = audit_v2.reduced_orders(case, a_mode)
                self.assertEqual({tuple(row["schedule"]) for row in c_rows},
                                 {tuple(row["schedule"]) for row in a_rows},
                                 f"{case['id']} {c_mode}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
