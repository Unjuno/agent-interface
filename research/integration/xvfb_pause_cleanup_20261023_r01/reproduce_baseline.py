"""Reproduce missing post-STOP cleanup with signal doubles and frozen source."""
from pathlib import Path
import subprocess
import sys
import types
import unittest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
BASE = "527d7a940c23dbbb6af3831dc6705eb2a24ef096"

if __name__ == "__main__":
    from runtime.cli_v1 import test_mcp_xvfb_blocked_release_integration as harness
    path = "runtime/cli_v1/test_mcp_xvfb_blocked_release_integration.py"
    source = subprocess.check_output(["git", "show", BASE + ":" + path], cwd=ROOT)
    baseline = types.ModuleType("runtime.cli_v1.baseline_xvfb_harness")
    baseline.__package__ = "runtime.cli_v1"
    exec(compile(source, BASE + ":" + path, "exec"), baseline.__dict__)
    harness._pause_owned_xvfb_for_test = baseline._pause_owned_xvfb_for_test
    suite = unittest.defaultTestLoader.loadTestsFromNames([
        "runtime.cli_v1.test_xvfb_pause_cleanup.XvfbPauseCleanupTests."
        "test_status_read_error_after_stop_resumes_exact_handle_and_closes_it",
        "runtime.cli_v1.test_xvfb_pause_cleanup.XvfbPauseCleanupTests."
        "test_timer_start_failure_after_stop_resumes_exact_handle",
    ])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)
