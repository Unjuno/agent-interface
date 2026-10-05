import importlib.util
import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).parent
A02 = ROOT.parent / "looming_yield_5905_boundary_jitter_a02_20261005"
A09 = ROOT.parent / "looming_yield_5905_image_only_t0_9_a09_20261005"
spec = importlib.util.spec_from_file_location("a03_generate", ROOT/"generate.py")
generate = importlib.util.module_from_spec(spec); spec.loader.exec_module(generate)
sys.path.insert(0, str(A09))
import candidate
import audit


class A03ConstructionTests(unittest.TestCase):
    def test_fresh_seed_exact_fixture_counts_and_truth_separation(self):
        with mock.patch.object(generate.base, "ROOT", ROOT), mock.patch.object(generate.base, "SEED", 20261011):
            data = generate.generate()
        self.assertEqual(generate.SEED, 20261011)
        self.assertEqual(len(data["manifest"]["cases"]), 36)
        self.assertEqual(sum(x["family"] == "approach" for x in data["truth"]["cases"]), 24)
        self.assertEqual(sum(x["family"] == "control" for x in data["truth"]["cases"]), 12)
        self.assertTrue(all("family" not in x and "jitter_px" not in x for x in data["manifest"]["cases"]))

    def test_frozen_current_a09_source_bytes(self):
        self.assertEqual(Path(candidate.__file__).read_bytes(), (A09/"candidate.py").read_bytes())
        self.assertEqual(Path(audit.__file__).read_bytes(), (A09/"audit.py").read_bytes())

    def test_mount_construction_rejects_bare_rw(self):
        source=(ROOT/"run_formal.py").read_text()
        self.assertNotIn(",rw\"", source)
        self.assertIn("network=none", source)


if __name__ == "__main__": unittest.main()
