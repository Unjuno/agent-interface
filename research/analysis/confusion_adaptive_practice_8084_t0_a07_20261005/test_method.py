"""Static tests only; candidate and auditor are invoked once by the run protocol."""
import ast
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).parent


class PackageTests(unittest.TestCase):
    def test_sources_parse(self):
        for path in (ROOT / "generate.py", ROOT / "candidate" / "candidate.py", ROOT / "auditor" / "auditor.py"):
            ast.parse(path.read_text(encoding="utf-8"), filename=str(path))

    def test_candidate_has_no_scoring_or_class_labels(self):
        source = (ROOT / "candidate" / "candidate.py").read_text(encoding="utf-8")
        for forbidden in ("SCORING.json", '"class"', "positive", "null", "latent", 'profile["rates"]'):
            self.assertNotIn(forbidden, source)

    def test_candidate_input_directory_is_scoped(self):
        names = sorted(p.name for p in (ROOT / "candidate").iterdir() if p.is_file())
        self.assertEqual(names, ["candidate.py"])


if __name__ == "__main__":
    unittest.main()
