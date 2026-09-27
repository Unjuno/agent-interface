"""Zero-update launcher/output-boundary checks; does not call runner.run_seed."""
import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("launcher", HERE / "construction_launcher.py")
launcher = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(launcher)


class LauncherBoundaryTests(unittest.TestCase):
    def test_logs_are_outside_fresh_empty_runner_output_and_success_receipt_retained(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source, output, logs = root / "source", root / "out", root / "logs"
            source.mkdir()
            (source / "construction.py").write_text("# test target\n", encoding="utf-8")
            def fake_run(command, **kwargs):
                target = Path(kwargs["env"]["NEEDLE_CONSTRUCTION_OUTPUT"])
                (target / "construction_raw.json").write_text("{}", encoding="utf-8")
                return type("Result", (), {"returncode": 0, "stdout": "ok\n", "stderr": ""})()
            with patch.object(launcher.subprocess, "run", side_effect=fake_run) as called:
                result = launcher.run(source, output, logs)
            self.assertEqual(result["status"], "CONSTRUCTION_EXIT_0")
            self.assertEqual(called.call_count, 1)
            self.assertEqual(sorted(p.name for p in output.iterdir()), ["construction_raw.json"])
            self.assertEqual(sorted(p.name for p in logs.iterdir()),
                             ["launcher_receipt.json", "stderr.txt", "stdout.txt"])

    def test_nonempty_output_stops_before_subprocess(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source, output, logs = root / "source", root / "out", root / "logs"
            source.mkdir(); output.mkdir(); (output / "occupied").touch()
            with patch.object(launcher.subprocess, "run") as called:
                result = launcher.run(source, output, logs)
            self.assertEqual(result["status"], "STOP_OUTPUT_NOT_EMPTY")
            called.assert_not_called()

    def test_colliding_directories_stop_before_subprocess(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); source = root / "source"
            source.mkdir(); (source / "construction.py").touch()
            with patch.object(launcher.subprocess, "run") as called:
                result = launcher.run(source, source, root / "logs")
            self.assertEqual(result["status"], "STOP_LAUNCH_PATH_ALIAS")
            called.assert_not_called()

    def test_nonempty_logs_stop_before_subprocess(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); source = root / "source"
            source.mkdir(); (source / "construction.py").touch()
            output, logs = root / "out", root / "logs"
            logs.mkdir(); (logs / "stale").touch()
            with patch.object(launcher.subprocess, "run") as called:
                result = launcher.run(source, output, logs)
            self.assertEqual(result["status"], "STOP_LOG_DIR_NOT_EMPTY")
            called.assert_not_called()


if __name__ == "__main__":
    unittest.main(verbosity=2)
