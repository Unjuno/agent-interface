import sys
import json
import tempfile
import unittest
from pathlib import Path
from types import ModuleType, SimpleNamespace
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

    def test_session_composes_v2_and_binds_its_sources(self):
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory)
            (out / "sources.json").write_text("{}", encoding="utf-8")
            base = ModuleType("session_map01_v12")
            base.Backend = object
            base.main = lambda: self.assertIs(base.Backend, telemetry.Backend)
            base.vd = SimpleNamespace()
            telemetry = ModuleType("doom_typed_release_backend_v2")
            telemetry.Backend = type("TelemetryBackend", (), {})
            with patch.dict(sys.modules, {
                    "session_map01_v12": base,
                    "doom_typed_release_backend_v2": telemetry}), \
                    patch.object(sys, "argv", ["session", "--out", str(out)]):
                session.main()
            self.assertIs(base.Backend, object)
            sources = json.loads((out / "sources.json").read_text())
            self.assertIn("doom/doom_typed_release_backend_v2.py", sources)
            self.assertIn("live_control/input_owner_v11.py", sources)
            self.assertIn("doom/map01_overlap_controller_v40.py", sources)


if __name__ == "__main__":
    unittest.main()
