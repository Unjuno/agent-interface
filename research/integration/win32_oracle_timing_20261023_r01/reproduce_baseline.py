"""Run current public timing regression with the frozen pre-fix caller owner."""
from pathlib import Path
import subprocess
import sys
import types
import unittest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
BASE = "46640f28c58302e224af5673658773745afca356"

if __name__ == "__main__":
    import runtime.cli_v1.owned_win32_session as owner_module
    path = "runtime/cli_v1/owned_win32_session.py"
    source = subprocess.check_output(["git", "show", BASE + ":" + path], cwd=ROOT)
    baseline = types.ModuleType("runtime.cli_v1.baseline_owned_win32_session")
    baseline.__package__ = "runtime.cli_v1"
    exec(compile(source, BASE + ":" + path, "exec"), baseline.__dict__)
    owner_module.OwnedWin32SessionOwner = baseline.OwnedWin32SessionOwner
    suite = unittest.defaultTestLoader.loadTestsFromName(
        "runtime.cli_v1.test_mcp_win32_composition.GuardedWin32PublicRouteTests."
        "test_public_task_oracle_rejects_stale_and_future_observation_times")
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)
