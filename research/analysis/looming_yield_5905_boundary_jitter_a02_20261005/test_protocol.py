import importlib.util
import json
import sys
import unittest
from unittest import mock
from pathlib import Path

ROOT = Path(__file__).parent
SRC = ROOT.parents[0] / "looming_yield_5905_image_only_t0_9_a09_20261005"
spec = importlib.util.spec_from_file_location("jitter_generate", ROOT / "generate.py")
generate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(generate)
sys.path.insert(0, str(SRC))
import candidate as candidate_src
import audit as audit_src


class BoundaryJitterConstructionTests(unittest.TestCase):
    def test_fixture_has_exact_frozen_counts_and_blinded_inputs(self):
        with mock.patch.object(generate, "ROOT", ROOT), mock.patch.object(generate, "SEED", 20261010):
            d = generate.generate()
        self.assertEqual(len(d["manifest"]["cases"]), 36)
        self.assertEqual(sum(x["family"] == "approach" for x in d["truth"]["cases"]), 24)
        self.assertEqual(sum(x["family"] == "control" for x in d["truth"]["cases"]), 12)
        self.assertTrue(all("family" not in c and "jitter_px" not in c for c in d["manifest"]["cases"]))
        self.assertEqual([x["timestamp_ms"] for x in d["manifest"]["cases"][0]["frames"]], generate.TIMES)

    def test_candidate_auditor_sources_are_unmodified_a09_bytes(self):
        self.assertEqual((SRC/"candidate.py").read_bytes(), Path(candidate_src.__file__).read_bytes())
        self.assertEqual((SRC/"audit.py").read_bytes(), Path(audit_src.__file__).read_bytes())

    def test_mount_runner_uses_no_bare_rw_field(self):
        source = (ROOT/"run_formal.py").read_text()
        self.assertNotIn(",rw\"", source)
        self.assertIn("network=none", source)


if __name__ == "__main__":
    unittest.main()
