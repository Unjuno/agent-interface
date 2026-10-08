import importlib.util,sys,unittest
from pathlib import Path
from unittest import mock
ROOT=Path(__file__).parent
A09=ROOT.parent/"looming_yield_5905_image_only_t0_9_a09_20261005"
spec=importlib.util.spec_from_file_location("a05_generate",ROOT/"generate.py")
generate=importlib.util.module_from_spec(spec);spec.loader.exec_module(generate)
sys.path.insert(0,str(A09));import candidate;import audit

class A06ConstructionTests(unittest.TestCase):
    def test_seed_counts_and_auditor_truth_contract(self):
        with mock.patch.object(generate.base,"ROOT",ROOT),mock.patch.object(generate.base,"SEED",20261014):d=generate.generate()
        self.assertEqual(generate.SEED,20261014)
        self.assertEqual(len(d["manifest"]["cases"]),36)
        self.assertEqual(sum(x["family"]=="approach" for x in d["truth"]),24)
        self.assertEqual(sum(x["family"]=="control" for x in d["truth"]),12)
        self.assertIsInstance(d["truth"],list)
        self.assertTrue(all("family" not in x and "jitter_px" not in x for x in d["manifest"]["cases"]))

    def test_current_a09_bytes_unchanged(self):
        self.assertEqual(Path(candidate.__file__).read_bytes(),(A09/"candidate.py").read_bytes())
        self.assertEqual(Path(audit.__file__).read_bytes(),(A09/"audit.py").read_bytes())

    def test_runner_uses_valid_rw_mount_and_fresh_main_gate(self):
        run=(ROOT/"run_formal.py").read_text();execute=(ROOT/"execute_formal.py").read_text()
        self.assertNotIn(",rw\"",run);self.assertIn("fetch",run)
        self.assertLess(execute.index("prepare_freeze.py"),execute.index("run_formal.py"))

if __name__=="__main__":unittest.main()
