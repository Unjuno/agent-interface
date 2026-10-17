"""Pre-freeze construction checks for audit-v3 claim normalization and scope."""
import json
import unittest
from pathlib import Path

import audit_v3

ROOT = Path(__file__).resolve().parent
MODEL = json.loads((ROOT / "MODEL.json").read_text())
RAW = json.loads((ROOT / "candidate_raw.json").read_text())


class AuditV3ConstructionTests(unittest.TestCase):
    def test_auditor_does_not_import_candidate(self):
        text = (ROOT / "audit_v3.py").read_text()
        self.assertNotIn("import candidate", text)
        self.assertNotIn("from candidate", text)

    def test_claims_are_compared_as_unordered_rows(self):
        normalize = lambda rows: sorted(audit_v3.packed(row) for row in rows)
        for case in MODEL["cases"]:
            for strategy, mode in (("predicate_dpor", "predicate"),
                                   ("mutant_missing_predicate", "node_only"),
                                   ("mutant_cross_scope", "mutant_cross_scope"),
                                   ("mutant_unknown_independent", "mutant_unknown_independent")):
                _, expected = audit_v3.reduced_orders(case, mode)
                stored = RAW["runs"]["claims"][strategy][case["id"]]
                self.assertEqual(normalize(stored), normalize(expected),
                                 f"{case['id']} {strategy}")

    def test_proposed_predicate_independence_claims_commute(self):
        for case in MODEL["cases"]:
            claims = RAW["runs"]["claims"]["predicate_dpor"][case["id"]]
            for claim in claims:
                if claim["declared_independent"]:
                    state = audit_v3.replay_prefix(case, claim["prefix"])
                    self.assertTrue(audit_v3.pair_commutes(
                        case, state, claim["prefix"], claim["left"], claim["right"]))


if __name__ == "__main__":
    unittest.main(verbosity=2)
