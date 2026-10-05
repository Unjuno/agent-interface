"""Run adjacent cancellation/release suites around the fault-injection test."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "research" / "live_control"))

from research.live_control.test_input_owner_v12_batch_release_intervals import BatchReleaseIntervalTests
from research.live_control.test_input_owner_v12_explicit_up_cancel import ExplicitKeyUpCancellationTests
from research.live_control.test_input_transition_owner_v4 import OwnerReceiptJoinTests
from research.doom.test_release_backend_v3_actual_composition import ActualReleaseCompositionTests
from research.live_control.test_executor_v13 import ExecutorV13Tests
from research.live_control.test_input_owner_v12_partial_release_failure import PartialReleaseFailureTests

loader = unittest.TestLoader()
suite = unittest.TestSuite()
suite.addTest(BatchReleaseIntervalTests(
    "test_cancelled_release_records_each_key_to_shared_sync_bound"))
suite.addTest(BatchReleaseIntervalTests(
    "test_restores_a_preloaded_owner_module_after_fake_xlib_run"))
suite.addTests(loader.loadTestsFromTestCase(OwnerReceiptJoinTests))
suite.addTests(loader.loadTestsFromTestCase(ExplicitKeyUpCancellationTests))
suite.addTests(loader.loadTestsFromTestCase(ActualReleaseCompositionTests))
suite.addTests(loader.loadTestsFromTestCase(ExecutorV13Tests))
suite.addTests(loader.loadTestsFromTestCase(PartialReleaseFailureTests))
suite.addTest(BatchReleaseIntervalTests(
    "test_cancelled_release_records_each_key_to_shared_sync_bound"))
result = unittest.TextTestRunner(verbosity=2).run(suite)
raise SystemExit(0 if result.wasSuccessful() else 1)
