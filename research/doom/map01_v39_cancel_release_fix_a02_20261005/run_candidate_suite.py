import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PACKAGE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from research.doom.map01_v39_cancel_release_fix_a02_20261005 import test_cancel_release as candidate_tests

suite = unittest.defaultTestLoader.loadTestsFromTestCase(candidate_tests.CancellationReceiptTests)
suite.addTests(unittest.defaultTestLoader.loadTestsFromName(
    "research.doom.map01_v39_cancel_release_fix_a02_20261005.test_release_record_durability"))
result = unittest.TextTestRunner(verbosity=2).run(suite)
sys.exit(0 if result.wasSuccessful() else 1)
