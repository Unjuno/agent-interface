from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


SOURCE_ROOT = Path(__file__).resolve().parents[1]


class SetupGoldenDemoOptInTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name) / "checkout"
        (self.root / "runtime").mkdir(parents=True)
        for name in (
            "setup-golden-demo.sh", "setup-golden-demo-v3.sh",
            "golden_desktop_demo.py", "golden_desktop_demo_v3.py",
            "requirements-golden.txt",
        ):
            shutil.copy2(SOURCE_ROOT / "runtime" / name, self.root / "runtime" / name)

    def tearDown(self):
        self.temp.cleanup()

    def run_setup(self, name, args=(), bindir=None):
        env = os.environ.copy()
        env["PATH"] = str(bindir or self.root) + os.pathsep + env.get("PATH", "")
        env["SETUP_STUB_LOG"] = str(self.root / "calls.txt")
        return subprocess.run(
            ["bash", str(self.root / "runtime" / name), *args],
            cwd=self.root, env=env, text=True, capture_output=True, check=False,
        )

    def test_setup_scripts_require_explicit_dependency_opt_in(self):
        for name in ("setup-golden-demo.sh", "setup-golden-demo-v3.sh"):
            with self.subTest(script=name):
                result = self.run_setup(name)
                self.assertEqual(result.returncode, 2)
                self.assertIn("--install-dependencies", result.stderr)
                self.assertFalse((self.root / "runtime" / ".venv").exists())
                self.assertFalse((self.root / "calls.txt").exists())

    def test_unexpected_argument_is_rejected_before_side_effects(self):
        for name in ("setup-golden-demo.sh", "setup-golden-demo-v3.sh"):
            with self.subTest(script=name):
                result = self.run_setup(name, ("--force",))
                self.assertEqual(result.returncode, 2)
                self.assertFalse((self.root / "calls.txt").exists())

    def test_existing_virtual_environment_is_not_overwritten(self):
        for name in ("setup-golden-demo.sh", "setup-golden-demo-v3.sh"):
            with self.subTest(script=name):
                venv = self.root / "runtime" / ".venv"
                venv.mkdir(exist_ok=True)
                marker = venv / "preserve-me"
                marker.write_text("existing", encoding="utf-8")
                result = self.run_setup(name, ("--install-dependencies",))
                self.assertEqual(result.returncode, 2)
                self.assertIn("already exists", result.stderr)
                self.assertEqual(marker.read_text(encoding="utf-8"), "existing")
                self.assertFalse((self.root / "calls.txt").exists())

    def test_opted_in_setup_invokes_venv_pip_and_doctor_in_order(self):
        for name, doctor in (
            ("setup-golden-demo.sh", "golden_desktop_demo.py"),
            ("setup-golden-demo-v3.sh", "golden_desktop_demo_v3.py"),
        ):
            with self.subTest(script=name):
                bindir = self.root / "bin"
                bindir.mkdir(exist_ok=True)
                stub = bindir / "python3"
                stub.write_text(
                    "#!/bin/sh\n"
                    "printf '%s\\n' \"$*\" >> \"$SETUP_STUB_LOG\"\n"
                    "if [ \"$1\" = -m ] && [ \"$2\" = venv ]; then\n"
                    "  mkdir -p \"$3/bin\"\n"
                    "  cat > \"$3/bin/python\" <<'PY'\n"
                    "#!/bin/sh\n"
                    "printf '%s\\n' \"$*\" >> \"$SETUP_STUB_LOG\"\n"
                    "exit 0\n"
                    "PY\n"
                    "  chmod +x \"$3/bin/python\"\n"
                    "fi\n"
                    "exit 0\n",
                    encoding="utf-8",
                )
                stub.chmod(0o755)
                result = self.run_setup(name, ("--install-dependencies",), bindir)
                self.assertEqual(result.returncode, 0, result.stderr)
                calls = (self.root / "calls.txt").read_text(encoding="utf-8").splitlines()
                venv = self.root / "runtime" / ".venv"
                self.assertEqual(calls[0], f"-m venv {venv}")
                self.assertIn("-m pip install --disable-pip-version-check", calls[1])
                self.assertEqual(calls[2], f"{self.root / 'runtime' / doctor} doctor")
                shutil.rmtree(venv)
                (self.root / "calls.txt").unlink()


if __name__ == "__main__":
    unittest.main()
