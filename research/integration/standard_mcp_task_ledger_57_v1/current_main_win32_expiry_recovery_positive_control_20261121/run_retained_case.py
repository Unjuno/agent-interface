"""Run one existing stdio recovery unittest while retaining its temp receipts."""
import os
import sys
import unittest
from pathlib import Path

import runtime.cli_v1.test_mcp_supervised_win32 as tests


class RetainedTemporaryDirectory:
    def __init__(self, *args, **kwargs):
        del args, kwargs
        self.path = Path(os.environ["AGENT_INTERFACE_TEST_EVIDENCE_DIR"])
        self.path.mkdir(parents=True, exist_ok=False)

    def __enter__(self):
        return str(self.path)

    def __exit__(self, *_exc):
        return False


tests.TemporaryDirectory = RetainedTemporaryDirectory
suite = unittest.TestSuite([tests.SupervisedWin32MCPTests(
    "test_production_stdio_orphan_recovery_pending_exact_query")])
result = unittest.TextTestRunner(verbosity=2).run(suite)
sys.exit(0 if result.wasSuccessful() else 1)
