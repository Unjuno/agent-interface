"""Run the selected guarded-MCP local suite with Windows spawn-safe entry."""
from __future__ import annotations
import importlib
import os
from pathlib import Path
import sys
import unittest
REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
SELECTED_MODULES = (
    "runtime.cli_v1.test_mcp_owned_process",
    "runtime.cli_v1.test_mcp_process_identity",
    "runtime.cli_v1.test_mcp_transport_cancellation",
    "runtime.cli_v1.test_mcp_wait_budget",
    "runtime.cli_v1.test_mcp_target_queries",
    "runtime.cli_v1.test_mcp_guarded",
    "runtime.cli_v1.test_mcp_server",
)
EXCLUDED_TESTS = frozenset({
    "runtime.cli_v1.test_mcp_server.PublicMCPTests.test_portable_stdio_runs_outside_checkout",
})
def _filter(test):
    if isinstance(test, unittest.TestSuite):
        return unittest.TestSuite(
            retained
            for child in test
            if (retained := _filter(child)) is not None
        )
    return None if test.id() in EXCLUDED_TESTS else test
def main() -> int:
    sys.path.insert(0, str(REPOSITORY_ROOT))
    inherited = os.environ.get("PYTHONPATH", "")
    os.environ["PYTHONPATH"] = os.pathsep.join(
        value for value in (str(REPOSITORY_ROOT), inherited) if value
    )
    loader = unittest.defaultTestLoader
    suite = unittest.TestSuite()
    for module_name in SELECTED_MODULES:
        module = importlib.import_module(module_name)
        suite.addTests(_filter(loader.loadTestsFromModule(module)))
    result = unittest.TextTestRunner(verbosity=1).run(suite)
    return 0 if result.wasSuccessful() else 1
if __name__ == "__main__":
    raise SystemExit(main())
