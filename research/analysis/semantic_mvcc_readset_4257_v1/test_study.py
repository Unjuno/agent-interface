import json,unittest
from pathlib import Path
import study
ROOT=Path(__file__).resolve().parent
CASES=json.loads((ROOT/'cases.json').read_text())
class T(unittest.TestCase):
 def test_count(self): self.assertEqual(len(CASES),10)
 def test_unchanged(self): self.assertTrue(study.snapshot(CASES[0])); self.assertTrue(study.readset(CASES[0]))
 def test_irrelevant_salvage(self): self.assertFalse(study.snapshot(CASES[1])); self.assertTrue(study.readset(CASES[1]))
 def test_dependency_change(self): self.assertFalse(study.readset(CASES[3])); self.assertFalse(study.readset(CASES[4]))
 def test_unknown(self): self.assertFalse(study.readset(CASES[5]))
 def test_versions(self): self.assertFalse(study.readset(CASES[6])); self.assertFalse(study.readset(CASES[7]))
 def test_aba(self): self.assertEqual(CASES[8]['start']['target'][0],CASES[8]['finish']['target'][0]); self.assertFalse(study.readset(CASES[8]))
 def test_deadline(self): self.assertFalse(study.readset(CASES[9]))
if __name__=='__main__': unittest.main(verbosity=2)
