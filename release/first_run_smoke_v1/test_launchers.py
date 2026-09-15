"""Real bash/exec tests with fail-closed Python dispatch doubles; no pip/GUI/model."""
from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

from preflight import FILES, SCRIPTS, inspect

ROOT = Path(__file__).resolve().parents[2]
# This double never imports the runtime or executes pip. Unknown calls fail closed.
DOUBLE = r'''import json, os, pathlib, shutil, sys
args = sys.argv[1:]
if args[:2] == ["-m", "venv"]: stage = "venv"
elif args[:3] == ["-m", "pip", "install"]: stage = "pip"
elif args and args[0].endswith("/golden_desktop_demo_v3.py"): stage = "entrypoint"
else: raise SystemExit(97)
with open(os.environ["SMOKE_LOG"], "a", encoding="utf-8") as f:
    f.write(json.dumps({"interpreter": str(pathlib.Path(__file__)), "stage": stage, "argv": args}) + "\n")
if os.environ.get("SMOKE_FAIL") == stage:
    raise SystemExit({"venv": 17, "pip": 23, "entrypoint": 31}[stage])
if stage == "venv":
    target = pathlib.Path(args[2]) / "bin" / "python"
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(__file__, target)
    target.chmod(0o755)
'''


class Fixture:
    def __init__(self, mode: int = 0o755):
        self.temp = tempfile.TemporaryDirectory(prefix="ai first run ")
        self.root = Path(self.temp.name) / "repository with spaces"
        self.bin = Path(self.temp.name) / "stub bin"
        self.bin.mkdir()
        self.log = Path(self.temp.name) / "dispatch.jsonl"
        for name in FILES:
            target = self.root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / name, target)
            target.chmod(mode if name in SCRIPTS else 0o644)
        (self.bin / "python3").write_text("#!" + sys.executable + "\n" + DOUBLE, encoding="utf-8")
        (self.bin / "python3").chmod(0o755)
        # Only the shell and dirname plus the double are available on PATH.
        for name in ("bash", "dirname"):
            os.symlink(shutil.which(name), self.bin / name)
        self.env = {"PATH": str(self.bin), "SMOKE_LOG": str(self.log), "LC_ALL": "C"}

    def close(self):
        self.temp.cleanup()

    def call(self, script: str, *args: str) -> dict:
        try:
            result = subprocess.run([str(self.root / script), *args], cwd=self.temp.name, env=self.env, text=True, capture_output=True, timeout=5)
            return {"returncode": result.returncode, "stdout": result.stdout, "stderr": result.stderr}
        except PermissionError as error:
            return {"returncode": None, "error": "PermissionError", "errno": error.errno}

    def calls(self) -> list:
        return [json.loads(line) for line in self.log.read_text().splitlines()] if self.log.exists() else []

    def venv(self):
        target = self.root / "runtime/.venv/bin/python"
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(self.bin / "python3", target)
        target.chmod(0o755)
        return target

    def git(self, *args):
        return subprocess.run(["git", "-C", str(self.root), *args], check=True, capture_output=True, text=True)

    def commit(self):
        self.git("init", "-q")
        self.git("config", "user.name", "Offline fixture")
        self.git("config", "user.email", "fixture@example.invalid")
        self.git("config", "core.filemode", "true")
        self.git("config", "core.autocrlf", "false")
        self.git("add", "runtime")
        self.git("-c", "commit.gpgsign=false", "commit", "-qm", "Disposable fixture; not project provenance")


@unittest.skipUnless(os.name == "posix" and shutil.which("bash") and shutil.which("git"), "POSIX, bash and git required")
class LauncherTests(unittest.TestCase):
    def setUp(self):
        self.f = Fixture()
        self.addCleanup(self.f.close)

    def test_retained_baseline_refuses_both_direct_entrypoints(self):
        for name in SCRIPTS:
            (self.f.root / name).chmod(0o644)
            result = self.f.call(name, "doctor")
            self.assertEqual(result.get("errno"), 13)
        self.assertEqual(self.f.calls(), [])

    def test_bash_syntax(self):
        for name in SCRIPTS:
            subprocess.run(["bash", "-n", str(self.f.root / name)], check=True)

    def test_fallback_doctor_from_other_directory_with_spaces(self):
        self.assertEqual(self.f.call(SCRIPTS[1], "doctor")["returncode"], 0)
        self.assertEqual(self.f.calls()[0]["argv"], [str(self.f.root / FILES[2]), "doctor"])
        self.assertEqual(self.f.calls()[0]["interpreter"], str(self.f.bin / "python3"))

    def test_venv_preferred(self):
        target = self.f.venv()
        self.assertEqual(self.f.call(SCRIPTS[1], "audit-retained")["returncode"], 0)
        self.assertEqual(self.f.calls()[0]["interpreter"], str(target))

    def test_nonexecutable_venv_falls_back(self):
        self.f.venv().chmod(0o644)
        self.assertEqual(self.f.call(SCRIPTS[1], "doctor")["returncode"], 0)
        self.assertEqual(self.f.calls()[0]["interpreter"], str(self.f.bin / "python3"))

    def test_default_run_dispatch_is_preserved_but_never_executed(self):
        self.assertEqual(self.f.call(SCRIPTS[1])["returncode"], 0)
        self.assertEqual(self.f.calls()[0]["argv"][-1], "run")

    def test_arguments_remain_literal(self):
        args = ("audit-live", "a b;$(echo NEVER_EXECUTED)")
        self.assertEqual(self.f.call(SCRIPTS[1], *args)["returncode"], 0)
        self.assertEqual(self.f.calls()[0]["argv"][1:], list(args))

    def test_missing_python_fails_without_any_dispatch(self):
        (self.f.bin / "python3").unlink()
        self.assertNotEqual(self.f.call(SCRIPTS[1], "doctor")["returncode"], 0)
        self.assertEqual(self.f.calls(), [])

    def test_setup_sequence(self):
        self.assertEqual(self.f.call(SCRIPTS[0])["returncode"], 0)
        calls = self.f.calls()
        self.assertEqual([c["stage"] for c in calls], ["venv", "pip", "entrypoint"])
        self.assertEqual(calls[1]["argv"], ["-m", "pip", "install", "--disable-pip-version-check", "-r", str(self.f.root / FILES[3])])
        self.assertEqual(calls[2]["argv"], [str(self.f.root / FILES[2]), "doctor"])

    def test_setup_failures_preserve_exit_status_and_stop(self):
        for stage, code, count in (("venv", 17, 1), ("pip", 23, 2), ("entrypoint", 31, 3)):
            with self.subTest(stage=stage):
                if self.f.log.exists(): self.f.log.unlink()
                self.f.env["SMOKE_FAIL"] = stage
                self.assertEqual(self.f.call(SCRIPTS[0])["returncode"], code)
                self.assertEqual(len(self.f.calls()), count)

    def test_archive_preflight_is_scoped(self):
        report = inspect(self.f.root)
        self.assertTrue(report["passed"])
        self.assertEqual(report["mode_source"], "archive_filesystem_only")
        self.assertIsNone(report["revision"])

    def test_missing_file_rejected(self):
        (self.f.root / FILES[2]).unlink()
        self.assertFalse(inspect(self.f.root)["passed"])

    def test_crlf_rejected(self):
        path = self.f.root / SCRIPTS[1]
        path.write_bytes(path.read_bytes().replace(b"\n", b"\r\n"))
        self.assertFalse(inspect(self.f.root)["passed"])

    def test_unpinned_and_duplicate_requirements_rejected(self):
        for data in ("", "Pillow>=10\n", "Pillow==10\npillow==11\n", "-r other.txt\n"):
            with self.subTest(data=data):
                (self.f.root / FILES[3]).write_text(data)
                self.assertFalse(inspect(self.f.root)["passed"])

    def test_syntax_error_rejected_without_import(self):
        (self.f.root / FILES[2]).write_text("def broken(:\n")
        self.assertFalse(inspect(self.f.root)["passed"])

    def test_symlink_rejected(self):
        path = self.f.root / SCRIPTS[1]
        data = path.read_bytes()
        path.unlink()
        target = Path(self.f.temp.name) / "external.sh"
        target.write_bytes(data)
        target.chmod(0o755)
        path.symlink_to(target)
        self.assertFalse(inspect(self.f.root)["passed"])

    def test_committed_git_modes_pass(self):
        self.f.commit()
        self.assertTrue(inspect(self.f.root)["passed"])

    def test_local_chmod_cannot_mask_bad_committed_modes(self):
        for name in SCRIPTS: (self.f.root / name).chmod(0o644)
        self.f.commit()
        for name in SCRIPTS: (self.f.root / name).chmod(0o755)
        self.assertFalse(inspect(self.f.root)["passed"])

    def test_checkout_permission_loss_rejected(self):
        self.f.commit()
        (self.f.root / SCRIPTS[1]).chmod(0o644)
        self.assertFalse(inspect(self.f.root)["passed"])

    def test_uncommitted_content_rejected(self):
        self.f.commit()
        with (self.f.root / FILES[2]).open("a") as stream: stream.write("\n# local edit\n")
        self.assertFalse(inspect(self.f.root)["passed"])

    def test_report_no_overwrite(self):
        out = Path(self.f.temp.name) / "result.json"
        command = [sys.executable, str(Path(__file__).with_name("preflight.py")), "--root", str(self.f.root), "--out", str(out)]
        self.assertEqual(subprocess.run(command, capture_output=True).returncode, 0)
        original = out.read_bytes()
        self.assertEqual(subprocess.run(command, capture_output=True).returncode, 2)
        self.assertEqual(out.read_bytes(), original)


if __name__ == "__main__":
    unittest.main(verbosity=2)
