import argparse
from pathlib import Path
import tempfile
import unittest

from session_command_adapter import build_session_command, install


class AdapterTest(unittest.TestCase):
    def test_forwards_existing_v39_runtime_contract_to_v16(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            session = root / "session_map01_v16.py"
            fixture = root / "fixture.json"
            session.touch()
            fixture.touch()
            args = argparse.Namespace(seed="17", load_fixture_manifest=str(fixture))
            command = build_session_command(args, root / "runtime", session, "/python")
            self.assertEqual(command, [
                "/python", str(session.resolve()), "--out", str((root / "runtime").resolve()),
                "--seed", "17", "--timeout-seconds", "600", "--skill", "1",
                "--load-fixture-manifest", str(fixture.resolve()),
            ])

    def test_rejects_wrong_version_and_missing_inputs(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            wrong = root / "session_map01_v12.py"
            wrong.touch()
            fixture = root / "fixture.json"
            fixture.touch()
            args = argparse.Namespace(seed="1", load_fixture_manifest=str(fixture))
            with self.assertRaisesRegex(ValueError, "session_map01_v16.py"):
                build_session_command(args, root / "out", wrong)
            with self.assertRaises(FileNotFoundError):
                build_session_command(args, root / "out", root / "missing-session_map01_v16.py")

    def test_install_changes_only_session_selector(self):
        class Controller:
            pass
        controller = Controller()
        controller.app_server_command = lambda: ["unchanged"]
        controller.win = lambda path: "unchanged"
        with tempfile.TemporaryDirectory() as directory:
            session = Path(directory) / "session_map01_v16.py"
            session.touch()
            install(controller, session)
            self.assertEqual(controller.app_server_command(), ["unchanged"])
            self.assertEqual(controller.win("x"), "unchanged")
            self.assertIn("session_map01_v16.py", controller.session_command(
                argparse.Namespace(seed="2", load_fixture_manifest=__file__), directory
            )[1])


if __name__ == "__main__":
    unittest.main(verbosity=2)
