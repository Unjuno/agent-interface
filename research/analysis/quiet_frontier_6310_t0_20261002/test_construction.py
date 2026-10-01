import ast
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).parent


class Construction(unittest.TestCase):
    def test_seven_frozen_cases(self):
        data = json.loads((ROOT / "fixture.json").read_text())
        self.assertEqual(len(data["cases"]), 7)
        self.assertEqual(len({x["id"] for x in data["cases"]}), 7)

    def test_frontier_and_actuation_are_distinct(self):
        source = (ROOT / "candidate.py").read_text()
        self.assertIn("QUIET_AS_OF_FRONTIER", source)
        self.assertIn("atomic_compare_at_B", source)
        self.assertIn('else "BLOCK"', source)

    def test_post_frontier_counterexample_exists(self):
        data = json.loads((ROOT / "fixture.json").read_text())
        row = next(x for x in data["cases"] if x["id"] == "change_after_F_before_B")
        self.assertGreater(row["version_B"], row["version_F"])
        self.assertFalse(row["atomic_compare_at_B"])

    def test_independent_auditor_import_boundary(self):
        tree = ast.parse((ROOT / "auditor.py").read_text())
        modules = {n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)}
        self.assertNotIn("candidate", modules)


if __name__ == "__main__":
    unittest.main()
