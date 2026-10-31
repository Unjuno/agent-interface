import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

import auditor
import candidate


class MutationAuditTests(unittest.TestCase):
    def test_formal_audit_executes_and_records_all_six_mutations(self):
        fixture = json.loads((ROOT / "input.json").read_text())
        truth = json.loads((ROOT / "truth.json").read_text())
        raw = candidate.run(fixture)
        result = auditor.audit(fixture, raw, truth)
        self.assertEqual("PASS_METHOD_SCOPED", result["disposition"])
        self.assertEqual(6, result["mutation_controls_rejected"])
        self.assertEqual(6, len(result["mutation_results"]))
        self.assertTrue(all(row["rejected"] and row["reason"] for row in result["mutation_results"]))

    def test_gate_fails_if_a_mutation_control_is_removed(self):
        fixture = json.loads((ROOT / "input.json").read_text())
        truth = json.loads((ROOT / "truth.json").read_text())
        raw = candidate.run(fixture)
        original = auditor._mutation_cases
        try:
            auditor._mutation_cases = lambda candidate, sealed: original(candidate, sealed)[:5]
            with self.assertRaisesRegex(ValueError, "mutation controls"):
                auditor.audit(fixture, raw, truth)
        finally:
            auditor._mutation_cases = original


if __name__ == "__main__":
    unittest.main()
