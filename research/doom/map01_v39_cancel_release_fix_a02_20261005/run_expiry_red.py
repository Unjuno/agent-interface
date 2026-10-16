import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PACKAGE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from research.doom.map01_v39_cancel_release_fix_a02_20261005 import test_cancel_release

test_cancel_release.BRIDGE_V2_PATH = PACKAGE / "bridge_v2_before.py"
case = test_cancel_release.CancellationReceiptTests(
    "test_executor_expiry_terminal_contains_one_verified_cleanup_receipt")
result = unittest.TextTestRunner(verbosity=2).run(unittest.TestSuite([case]))
sys.exit(0 if result.wasSuccessful() else 1)
