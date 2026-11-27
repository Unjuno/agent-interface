"""Run the single composed Fake X lifecycle check/use discriminator."""
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from runtime.cli_v1.test_mcp_window_lifecycle import LifecycleMCPTests

case = LifecycleMCPTests('test_destroy_between_final_check_and_xtest_emit')
result = unittest.TextTestRunner(verbosity=2).run(case)
if not result.wasSuccessful():
    raise SystemExit(1)
print(json.dumps(case.lifecycle_race_receipt, sort_keys=True, indent=2))
