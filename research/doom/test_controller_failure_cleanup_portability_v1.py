"""Windows-style discovery must not import POSIX-only test dependencies."""
import subprocess
import sys
import unittest
from pathlib import Path


HERE = Path(__file__).resolve().parent


class CleanupTestPortabilityTests(unittest.TestCase):
    def test_test_module_can_be_discovered_without_fcntl(self):
        script = r'''import importlib.abc, sys, unittest
class BlockFcntl(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname == "fcntl":
            raise ModuleNotFoundError("No module named 'fcntl'")
sys.meta_path.insert(0, BlockFcntl())
sys.path.insert(0, sys.argv[1])
suite = unittest.defaultTestLoader.loadTestsFromName("test_controller_failure_cleanup_v1")
tests = list(suite)
failed_imports = [test for test in tests if type(test).__name__ == "_FailedTest"]
print(f"tests={suite.countTestCases()} import_errors={len(failed_imports)}")
if failed_imports:
    print(failed_imports[0]._exception)
'''
        completed = subprocess.run(
            [sys.executable, "-c", script, str(HERE)],
            capture_output=True, text=True, check=False)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(
            completed.stdout.strip(), "tests=8 import_errors=0",
            completed.stderr)


if __name__ == "__main__":
    unittest.main()
