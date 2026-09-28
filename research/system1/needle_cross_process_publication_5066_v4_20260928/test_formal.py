import unittest

from formal import IMAGE, auditor_command, main, runner_command
from unittest import mock
from types import SimpleNamespace


def mounts(command):
    return [command[index + 1] for index, token in enumerate(command[:-1])
            if token == "--mount"]


class ContainerBoundaryTests(unittest.TestCase):
    def test_auditor_reads_raw_read_only_and_writes_only_separate_output(self):
        source = "type=bind,source=C:/study,target=/src,readonly"
        raw = "type=bind,source=C:/evidence/raw,target=/raw,readonly"
        audit = "type=bind,source=C:/evidence/audit,target=/audit"
        command = auditor_command(source, raw, audit)
        self.assertEqual(command[:5], ["docker", "--context", "desktop-linux", "run", "--rm"])
        self.assertEqual(mounts(command), [source, raw, audit])
        self.assertEqual(command[-3:], [IMAGE, "python", "/src/audit.py"])
        self.assertIn("readonly", mounts(command)[1])
        self.assertNotIn("readonly", mounts(command)[2])
        self.assertNotEqual(mounts(command)[1].split(",source=", 1)[1].split(",", 1)[0],
                            mounts(command)[2].split(",source=", 1)[1].split(",", 1)[0])

    def test_runner_has_its_own_raw_write_mount(self):
        source = "type=bind,source=C:/study,target=/src,readonly"
        raw_write = "type=bind,source=C:/evidence/raw,target=/out"
        command = runner_command(source, raw_write)
        self.assertEqual(mounts(command), [source, raw_write])
        self.assertEqual(command[-3:], [IMAGE, "python", "/src/runner.py"])

    def test_auditor_runs_after_runner_nonzero_when_raw_receipt_exists(self):
        checks = {
            "running_containers": [], "docker_context": "desktop-linux",
            "docker_engine": "test", "docker_version_image": IMAGE,
            "source_checks": {},
        }
        runner = SimpleNamespace(returncode=1, stdout="partial", stderr="failed")
        auditor = SimpleNamespace(returncode=1, stdout="STOP", stderr="")
        with mock.patch("formal.preflight", return_value=checks), \
             mock.patch("formal.run", side_effect=[runner, auditor]) as run_mock, \
             mock.patch("pathlib.Path.mkdir"), \
             mock.patch("pathlib.Path.is_file", return_value=True), \
             mock.patch("pathlib.Path.write_text"), \
             mock.patch("pathlib.Path.rglob", return_value=[]):
            with mock.patch("sys.argv", ["formal.py", "--output", "C:/fresh/result"]):
                self.assertEqual(main(), 1)
            self.assertEqual(run_mock.call_count, 2)

    def test_auditor_not_run_when_runner_wrote_no_raw_receipt(self):
        checks = {
            "running_containers": [], "docker_context": "desktop-linux",
            "docker_engine": "test", "docker_version_image": IMAGE,
            "source_checks": {},
        }
        runner = SimpleNamespace(returncode=1, stdout="", stderr="failed")
        with mock.patch("formal.preflight", return_value=checks), \
             mock.patch("formal.run", return_value=runner) as run_mock, \
             mock.patch("pathlib.Path.mkdir"), \
             mock.patch("pathlib.Path.is_file", return_value=False), \
             mock.patch("pathlib.Path.write_text"), \
             mock.patch("pathlib.Path.rglob", return_value=[]):
            with mock.patch("sys.argv", ["formal.py", "--output", "C:/fresh/result"]):
                self.assertEqual(main(), 1)
            self.assertEqual(run_mock.call_count, 1)


if __name__ == "__main__":
    unittest.main()
