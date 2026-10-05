import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
V16_SOURCE = REPO / "research/doom/acknowledged_scorer_59_4d74_20261004/source"
sys.path.insert(0, str(V16_SOURCE))
sys.path.insert(0, str(ROOT))

from acknowledged_scorer_v1 import AcknowledgedSampler
import session_map01_v17 as session
from state_snapshot_sampler import coherent_snapshot_sample


class V17SessionWiringTests(unittest.TestCase):
    def test_installs_snapshot_sampler_restores_and_binds_source_hashes(self):
        original = session.previous._coherent_progress_sample
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory)
            (out / "sources.json").write_text("{}", encoding="utf-8")

            def fake_run():
                installed = session.previous._coherent_progress_sample
                self.assertIsInstance(installed, AcknowledgedSampler)
                self.assertIs(installed.sample_fn, coherent_snapshot_sample)
                return "session-returned"

            with patch.object(session.previous, "_option", return_value=str(out)), \
                    patch.object(session.previous, "main", side_effect=fake_run):
                self.assertEqual(session.main(), "session-returned")

            self.assertIs(session.previous._coherent_progress_sample, original)
            manifest = json.loads((out / "sources.json").read_text(encoding="utf-8"))
            for name in ("session_map01_v17.py", "state_snapshot_sampler.py",
                         "acknowledged_scorer_v1.py"):
                self.assertEqual(len(manifest["doom/" + name]), 64)

    def test_restores_original_sampler_when_v15_session_raises(self):
        original = session.previous._coherent_progress_sample
        with tempfile.TemporaryDirectory() as directory:
            with patch.object(session.previous, "_option", return_value=directory), \
                    patch.object(session.previous, "main", side_effect=OSError("session failed")):
                with self.assertRaisesRegex(OSError, "session failed"):
                    session.main()
        self.assertIs(session.previous._coherent_progress_sample, original)


if __name__ == "__main__":
    unittest.main()
