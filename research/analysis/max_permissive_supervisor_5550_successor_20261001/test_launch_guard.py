import unittest
from datetime import datetime, timedelta, timezone
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
from unittest.mock import Mock

from launch_guard import assess, main


class LaunchGuardTests(unittest.TestCase):
    def setUp(self):
        self.freeze = {
            "allocation": "successor-03",
            "frozen_main": "abc123",
            "execution_lease": {
                "assigned": True,
                "coordinator_comment_id": "123456",
                "owner": "Unjuno",
                "start_utc": "2026-10-01T16:00:00Z",
                "end_utc": "2026-10-01T16:15:00Z",
                "image_digest": "sha256:abc",
                "platform": "linux/arm64",
            },
        }
        self.now = datetime(2026, 10, 1, 16, 0, tzinfo=timezone.utc)
        self.kwargs = dict(current_main="abc123", image_digest="sha256:abc",
                           platform="linux/arm64", running_containers=[], now=self.now)

    def test_exact_assigned_window_start_is_allowed(self):
        self.assertEqual(assess(self.freeze, **self.kwargs)["status"], "PASS_PRELAUNCH_GATE")

    def test_missing_assignment_fails_closed(self):
        self.freeze["execution_lease"]["assigned"] = False
        self.assertEqual(assess(self.freeze, **self.kwargs)["status"], "STOP_NO_EXPLICIT_ASSIGNMENT")

    def test_assignment_without_provenance_fails_closed(self):
        del self.freeze["execution_lease"]["coordinator_comment_id"]
        self.assertEqual(assess(self.freeze, **self.kwargs)["status"], "STOP_ASSIGNMENT_PROVENANCE_INCOMPLETE")

    def test_wrong_main_fails_closed(self):
        self.kwargs["current_main"] = "different"
        self.assertEqual(assess(self.freeze, **self.kwargs)["status"], "STOP_MAIN_MISMATCH")

    def test_wrong_digest_or_platform_fails_closed(self):
        self.kwargs["image_digest"] = "sha256:other"
        self.assertEqual(assess(self.freeze, **self.kwargs)["status"], "STOP_IMAGE_OR_PLATFORM_MISMATCH")

    def test_active_container_fails_closed(self):
        self.kwargs["running_containers"] = ["owned-by-other-task"]
        self.assertEqual(assess(self.freeze, **self.kwargs)["status"], "STOP_RESOURCE_OCCUPIED")

    def test_before_window_fails_closed(self):
        self.kwargs["now"] = datetime(2026, 10, 1, 15, 59, 59, tzinfo=timezone.utc)
        self.assertEqual(assess(self.freeze, **self.kwargs)["status"], "STOP_OUTSIDE_ASSIGNED_WINDOW")

    def test_end_boundary_is_exclusive(self):
        self.kwargs["now"] = datetime(2026, 10, 1, 16, 15, tzinfo=timezone.utc)
        self.assertEqual(assess(self.freeze, **self.kwargs)["status"], "STOP_OUTSIDE_ASSIGNED_WINDOW")

    def test_naive_time_is_rejected_by_cli_parser(self):
        from launch_guard import parse_utc
        with self.assertRaises(ValueError):
            parse_utc("2026-10-01T16:00:00")

    def test_cli_rejects_caller_supplied_clock(self):
        now = datetime.now(timezone.utc)
        start = now + timedelta(minutes=10)
        freeze = {
            "allocation": "successor-03",
            "frozen_main": "abc123",
            "execution_lease": {
                "assigned": True,
                "coordinator_comment_id": "123456",
                "owner": "Unjuno",
                "start_utc": start.isoformat(),
                "end_utc": (start + timedelta(minutes=10)).isoformat(),
                "image_digest": "sha256:abc",
                "platform": "linux/arm64",
            },
        }
        runner = Mock(return_value=SimpleNamespace(stdout=""))
        with tempfile.TemporaryDirectory() as temp_dir:
            freeze_path = Path(temp_dir) / "freeze.json"
            freeze_path.write_text(json.dumps(freeze), encoding="utf-8")
            with redirect_stderr(StringIO()), self.assertRaises(SystemExit) as raised:
                main(
                    [str(freeze_path), "--main-sha", "abc123",
                 "--image-digest", "sha256:abc", "--platform", "linux/arm64",
                     "--docker-context", "orbstack", "--now-utc", start.isoformat()],
                    runner=runner,
                )
        self.assertEqual(raised.exception.code, 2)
        runner.assert_not_called()

    def test_cli_requires_live_docker_inventory_context(self):
        now = datetime.now(timezone.utc)
        freeze = {
            "allocation": "successor-03",
            "frozen_main": "abc123",
            "execution_lease": {
                "assigned": True,
                "coordinator_comment_id": "123456",
                "owner": "Unjuno",
                "start_utc": (now - timedelta(minutes=1)).isoformat(),
                "end_utc": (now + timedelta(minutes=1)).isoformat(),
                "image_digest": "sha256:abc",
                "platform": "linux/arm64",
            },
        }
        script = Path(__file__).with_name("launch_guard.py")
        with tempfile.TemporaryDirectory() as temp_dir:
            freeze_path = Path(temp_dir) / "freeze.json"
            freeze_path.write_text(json.dumps(freeze), encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(script), str(freeze_path), "--main-sha", "abc123",
                 "--image-digest", "sha256:abc", "--platform", "linux/arm64"],
                capture_output=True, text=True, check=False,
            )
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn("PASS_PRELAUNCH_GATE", result.stdout)

    def test_live_inventory_stops_when_any_container_is_running(self):
        now = datetime.now(timezone.utc)
        freeze = {
            "allocation": "successor-03",
            "frozen_main": "abc123",
            "execution_lease": {
                "assigned": True,
                "coordinator_comment_id": "123456",
                "owner": "Unjuno",
                "start_utc": (now - timedelta(minutes=1)).isoformat(),
                "end_utc": (now + timedelta(minutes=1)).isoformat(),
                "image_digest": "sha256:abc",
                "platform": "linux/arm64",
            },
        }
        runner = Mock(return_value=SimpleNamespace(stdout="container-123\n"))
        output = StringIO()
        with tempfile.TemporaryDirectory() as temp_dir:
            freeze_path = Path(temp_dir) / "freeze.json"
            freeze_path.write_text(json.dumps(freeze), encoding="utf-8")
            with redirect_stdout(output):
                exit_code = main(
                    [str(freeze_path), "--main-sha", "abc123", "--image-digest",
                     "sha256:abc", "--platform", "linux/arm64", "--docker-context", "orbstack"],
                    runner=runner,
                )
        self.assertEqual(exit_code, 2)
        self.assertEqual(json.loads(output.getvalue())["status"], "STOP_RESOURCE_OCCUPIED")
        runner.assert_called_once_with(
            ["docker", "--context", "orbstack", "ps", "--quiet"],
            check=True, capture_output=True, text=True, timeout=10,
        )

    def test_invalid_lease_does_not_query_docker(self):
        freeze = {
            "allocation": "successor-03",
            "frozen_main": "abc123",
            "execution_lease": {"assigned": False},
        }
        runner = Mock(side_effect=AssertionError("Docker queried before lease validation"))
        output = StringIO()
        with tempfile.TemporaryDirectory() as temp_dir:
            freeze_path = Path(temp_dir) / "freeze.json"
            freeze_path.write_text(json.dumps(freeze), encoding="utf-8")
            with redirect_stdout(output):
                exit_code = main(
                    [str(freeze_path), "--main-sha", "abc123", "--image-digest",
                     "sha256:abc", "--platform", "linux/arm64", "--docker-context", "orbstack"],
                    runner=runner,
                )
        self.assertEqual(exit_code, 2)
        self.assertEqual(json.loads(output.getvalue())["status"], "STOP_NO_EXPLICIT_ASSIGNMENT")
        runner.assert_not_called()

    def test_failed_inventory_probe_fails_closed(self):
        now = datetime.now(timezone.utc)
        freeze = {
            "allocation": "successor-03",
            "frozen_main": "abc123",
            "execution_lease": {
                "assigned": True,
                "coordinator_comment_id": "123456",
                "owner": "Unjuno",
                "start_utc": (now - timedelta(minutes=1)).isoformat(),
                "end_utc": (now + timedelta(minutes=1)).isoformat(),
                "image_digest": "sha256:abc",
                "platform": "linux/arm64",
            },
        }
        runner = Mock(side_effect=subprocess.CalledProcessError(1, ["docker", "ps"]))
        output = StringIO()
        with tempfile.TemporaryDirectory() as temp_dir:
            freeze_path = Path(temp_dir) / "freeze.json"
            freeze_path.write_text(json.dumps(freeze), encoding="utf-8")
            with redirect_stdout(output):
                exit_code = main(
                    [str(freeze_path), "--main-sha", "abc123", "--image-digest",
                     "sha256:abc", "--platform", "linux/arm64", "--docker-context", "orbstack"],
                    runner=runner,
                )
        self.assertEqual(exit_code, 2)
        self.assertEqual(json.loads(output.getvalue())["status"], "STOP_DOCKER_INVENTORY_UNAVAILABLE")
        runner.assert_called_once()


if __name__ == "__main__":
    unittest.main()
