"""Reproduce premature compensation with frozen pre-fix custody/caller classes."""
from pathlib import Path
import importlib
import subprocess
import sys
import types
import unittest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
BASE = "572b86b6b1119d537d3fac20d2e6610e7e161a4f"

if __name__ == "__main__":
    for name, attribute in [
        ("runtime.guarded_win32_v1.operation_owner", "OperationOwner"),
        ("runtime.cli_v1.owned_win32_session", "OwnedWin32SessionOwner"),
    ]:
        path = name.replace(".", "/") + ".py"
        source = subprocess.check_output(["git", "show", BASE + ":" + path], cwd=ROOT)
        baseline = types.ModuleType(name + "_baseline")
        baseline.__package__ = name.rsplit(".", 1)[0]
        exec(compile(source, BASE + ":" + path, "exec"), baseline.__dict__)
        setattr(importlib.import_module(name), attribute, getattr(baseline, attribute))
    suite = unittest.defaultTestLoader.loadTestsFromName(
        "runtime.cli_v1.test_mcp_win32_backend_composition.GuardedWin32BackendCompositionTests."
        "test_cancel_during_final_generation_read_sends_no_compensating_input")
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)
