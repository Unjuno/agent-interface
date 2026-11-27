"""Run final regression against the frozen pre-fix owner without editing files."""
from pathlib import Path
import subprocess
import sys
import types
import unittest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
BASE = "6ee0c639b40322eff2a5d580cbc549eadb664ac4"
SOURCE = "runtime/cli_v1/owned_win32_session.py"

if __name__ == "__main__":
    import runtime.cli_v1.owned_win32_session as owner_module
    source = subprocess.check_output(["git", "show", BASE + ":" + SOURCE], cwd=ROOT)
    baseline = types.ModuleType("runtime.cli_v1.baseline_owned_win32_session")
    baseline.__package__ = "runtime.cli_v1"
    exec(compile(source, BASE + ":" + SOURCE, "exec"), baseline.__dict__)
    owner_module.OwnedWin32SessionOwner = baseline.OwnedWin32SessionOwner
    suite = unittest.defaultTestLoader.loadTestsFromName(
        "runtime.cli_v1.test_mcp_win32_composition.GuardedWin32PublicRouteTests."
        "test_target_generation_is_rechecked_after_admission_and_before_start_gate")
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)
