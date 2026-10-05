import importlib.util
import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT=Path(__file__).parent
A09=ROOT.parent/"looming_yield_5905_image_only_t0_9_a09_20261005"
spec=importlib.util.spec_from_file_location("a04_generate",ROOT/"generate.py")
generate=importlib.util.module_from_spec(spec); spec.loader.exec_module(generate)
sys.path.insert(0,str(A09)); import candidate; import audit

class A04ConstructionTests(unittest.TestCase):
    def test_fresh_seed_counts_and_candidate_truth_separation(self):
        with mock.patch.object(generate.base,"ROOT",ROOT),mock.patch.object(generate.base,"SEED",20261012):
            data=generate.generate()
        self.assertEqual(generate.SEED,20261012)
        self.assertEqual((len(data["manifest"]["cases"]),sum(x["family"]=="approach" for x in data["truth"]["cases"]),sum(x["family"]=="control" for x in data["truth"]["cases"])),(36,24,12))
        self.assertTrue(all("family" not in x and "jitter_px" not in x for x in data["manifest"]["cases"]))

    def test_reference_sources_match_current_main_bytes(self):
        self.assertEqual(Path(candidate.__file__).read_bytes(),(A09/"candidate.py").read_bytes())
        self.assertEqual(Path(audit.__file__).read_bytes(),(A09/"audit.py").read_bytes())

    def test_one_shot_mount_syntax_and_gate_order(self):
        run=(ROOT/"run_formal.py").read_text(); execute=(ROOT/"execute_formal.py").read_text()
        self.assertNotIn(",rw\"",run); self.assertIn("network=none",run)
        self.assertLess(execute.index("prepare_freeze.py"),execute.index("run_formal.py"))

if __name__=="__main__": unittest.main()
