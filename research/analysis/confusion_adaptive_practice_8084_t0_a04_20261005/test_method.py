"""Static isolation and syntax checks; deliberately does not execute candidate or auditor."""
import ast
import unittest
from pathlib import Path

ROOT = Path(__file__).parent


class IsolationTests(unittest.TestCase):
    def test_sources_parse(self):
        for path in (ROOT / "generate.py", ROOT / "candidate" / "candidate.py", ROOT / "auditor" / "auditor.py"):
            ast.parse(path.read_text(encoding="utf-8"), filename=str(path))

    def test_candidate_source_has_no_hidden_truth_or_imported_scorer(self):
        source = (ROOT / "candidate" / "candidate.py").read_text(encoding="utf-8")
        for forbidden in ("SCORING.json", "expected_top_pair", "stratum-01", "auditor"):
            self.assertNotIn(forbidden, source)

    def test_candidate_directory_has_only_declared_mount_inputs(self):
        names = sorted(p.name for p in (ROOT / "candidate").iterdir() if p.is_file())
        self.assertTrue(set(names).issubset({"candidate.py", "observed_counts.json"}))
        self.assertIn("candidate.py", names)


if __name__ == "__main__":
    unittest.main()
