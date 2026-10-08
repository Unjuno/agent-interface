import importlib.util
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent


def load(name):
    spec = importlib.util.spec_from_file_location(name, HERE / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


candidate = load("candidate")
audit = load("audit")


class ContractTests(unittest.TestCase):
    def test_exact_960_rows_and_cell_balance(self):
        rows = candidate.rows()
        self.assertEqual(len(rows), 960)
        self.assertEqual(len({r["uid"] for r in rows}), 960)
        self.assertEqual(audit.errors(rows), [])

    def test_provenance_mutation_rejected(self):
        rows = candidate.rows()
        rows[0]["embedded_source"] = "trusted_user"
        self.assertIn("embedded_provenance", audit.errors(rows))

    def test_hidden_target_mutation_rejected(self):
        rows = candidate.rows()
        rows[0]["geometry"]["visible"] = False
        self.assertIn("visibility_geometry", audit.errors(rows))

    def test_semantic_claim_cannot_be_promoted_without_adjudication(self):
        rows = candidate.rows()
        rows[0]["semantic_equivalence"] = "ACCEPTED"
        self.assertIn("adjudication_status", audit.errors(rows))


if __name__ == "__main__":
    unittest.main()
