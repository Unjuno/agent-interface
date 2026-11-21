import os
import sys
import tempfile
from pathlib import Path

evidence_dir = Path(__file__).resolve().parent
package_dir = evidence_dir.parent
worktree_root = package_dir.parents[2]
sys.path.insert(0, str(package_dir))
temp_root = tempfile.TemporaryDirectory(prefix="issue57-tests-", dir=worktree_root)
os.environ.update(TEMP=temp_root.name, TMP=temp_root.name, TMPDIR=temp_root.name)
import unittest

loader = unittest.defaultTestLoader
suite = unittest.TestSuite([
    loader.loadTestsFromName("test_effect_receipt_handoff_v1"),
    loader.loadTestsFromName("test_comparison_measurement_v1"),
    loader.loadTestsFromName("test_effect_receipt_reuse_horizon_integration_v1"),
])
try:
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    exit_code = 0 if result.wasSuccessful() else 1
finally:
    temp_root.cleanup()
sys.exit(exit_code)
