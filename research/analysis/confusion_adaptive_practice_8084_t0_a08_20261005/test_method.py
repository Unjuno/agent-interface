"""Construction checks; no fixture generator, candidate, or auditor calls."""
import ast
import unittest
from pathlib import Path

ROOT = Path(__file__).parent


class PackageTests(unittest.TestCase):
    def test_sources_parse(self):
        for path in (ROOT / "generate.py", ROOT / "candidate" / "candidate.py", ROOT / "auditor" / "auditor.py"):
            ast.parse(path.read_text(encoding="utf-8"), filename=str(path))

    def test_candidate_has_no_truth_labels(self):
        source = (ROOT / "candidate" / "candidate.py").read_text(encoding="utf-8")
        for forbidden in ("SCORING.json", '"class"', "positive", "null", "latent", 'profile["rates"]'):
            self.assertNotIn(forbidden, source)

    def test_candidate_directory_initial_allowlist(self):
        names = sorted(path.name for path in (ROOT / "candidate").iterdir() if path.is_file())
        self.assertEqual(names, ["candidate.py"])

    def test_formal_boundary_prerequisites_are_explicit(self):
        protocol = (ROOT / "PROTOCOL.md").read_text(encoding="utf-8")
        self.assertIn("git add --sparse", protocol)
        self.assertIn("require exit 0", protocol)
        self.assertIn("all remain uncalled", protocol)


if __name__ == "__main__":
    unittest.main()
