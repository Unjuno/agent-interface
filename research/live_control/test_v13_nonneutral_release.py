"""Run isolated fake-X custody regressions without mutating test-suite imports."""
import os
from pathlib import Path
import subprocess
import sys
import unittest


class NonNeutralReleaseTests(unittest.TestCase):
    def test_fake_x_release_failures_and_neutral_control(self):
        here = Path(__file__).resolve().parent
        env = os.environ.copy()
        env["OWNER_SOURCE_PATH"] = str(here / "input_owner_v13.py")
        env["PYTHONPATH"] = str(here)
        command = [sys.executable, "-B"]
        if sys.flags.optimize:
            command.append("-O")
        command.extend([str(here / "fixtures" / "v13_nonneutral_release_fixture.py"), "-q"])
        result = subprocess.run(command,
            env=env, capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
