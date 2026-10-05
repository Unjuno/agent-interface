import importlib.util
import json
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("t5_audit", HERE / "audit.py")
t5 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(t5)
ROOT = HERE.parents[2]
meta = json.loads((HERE / "audit_input.json").read_text())
spec_doc = json.loads((ROOT / meta["spec_path"]).read_text())
raw_doc = json.loads((ROOT / meta["raw_path"]).read_text())


class AuditOnlyPreflight(unittest.TestCase):
    def test_saved_t4_raw_reconstructs(self):
        self.assertEqual(t5.check(spec_doc, raw_doc)[0], [])

    def test_scientific_controls(self):
        self.assertTrue(all(t5.classify(spec_doc, raw_doc).values()))

    def test_four_corruption_controls(self):
        self.assertEqual(t5.mutation_rejections(spec_doc, raw_doc), [True] * 4)


if __name__ == "__main__":
    unittest.main()
