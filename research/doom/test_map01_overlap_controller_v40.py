import sys
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from types import ModuleType
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import map01_overlap_controller_v40 as candidate
import session_map01_v14 as session


class V40CompositionTests(unittest.TestCase):
    def test_session_command_selects_additive_v14_runner(self):
        class Args:
            seed = 17
            load_fixture_manifest = Path("fixture.json")
        command = candidate.session_command(Args(), Path("runtime"))
        self.assertEqual(Path(command[1]).name, "session_map01_v14.py")
        self.assertEqual(command[command.index("--out") + 1], "runtime")
        self.assertIn("--load-fixture-manifest", command)

    def test_session_uses_v13_feedback_and_binds_release_sources(self):
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory)
            prior_sources = {
                "doom/session_map01_v13.py": "v13",
                "doom/doom_retained_input_backend_v3.py": "release-v3",
                "live_control/input_transition_owner_v3.py": "owner-v3",
            }
            (out / "sources.json").write_text(json.dumps(prior_sources),
                                              encoding="utf-8")
            pipeline = ModuleType("session_map01_v13")
            pipeline.main = lambda: None
            with patch.dict(sys.modules, {"session_map01_v13": pipeline}), \
                    patch.object(sys, "argv", ["session", "--out", str(out)]):
                session.main()
            sources = json.loads((out / "sources.json").read_text())
            self.assertEqual(sources["doom/session_map01_v13.py"], "v13")
            self.assertEqual(sources["doom/doom_retained_input_backend_v3.py"],
                             "release-v3")
            self.assertEqual(sources["live_control/input_transition_owner_v3.py"],
                             "owner-v3")
            for source in ("session_map01_v14.py",
                           "map01_overlap_controller_v39.py",
                           "map01_overlap_controller_v40.py"):
                key = f"doom/{source}"
                digest = hashlib.sha256((HERE / source).read_bytes()).hexdigest()
                self.assertEqual(sources[key], digest)


if __name__ == "__main__":
    unittest.main()
