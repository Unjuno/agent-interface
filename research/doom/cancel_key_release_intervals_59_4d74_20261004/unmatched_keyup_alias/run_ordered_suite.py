"""Place the alias regression around adjacent fake-Xlib owner suites."""
import unittest
import io
from pathlib import Path

from research.live_control.test_input_owner_v12_unmatched_keyup_alias import (
    UnmatchedKeyUpAliasTests,
)
from research.live_control.test_input_owner_v12_explicit_keyup_keymap import (
    ExplicitKeyupKeymapTests,
)
from research.live_control.test_input_owner_v12_batch_release_intervals import (
    BatchReleaseIntervalTests,
)
from research.live_control.test_input_owner_v12_explicit_up_cancel import (
    ExplicitKeyUpCancellationTests,
)
from research.live_control.test_input_transition_owner_v4 import OwnerReceiptJoinTests
from research.live_control.test_executor_v13 import ExecutorV13Tests
from research.doom.test_release_backend_v3_actual_composition import (
    ActualReleaseCompositionTests,
)

loader = unittest.TestLoader()
suite = unittest.TestSuite()
suite.addTests(loader.loadTestsFromTestCase(UnmatchedKeyUpAliasTests))
suite.addTests(loader.loadTestsFromTestCase(ExplicitKeyupKeymapTests))
suite.addTest(BatchReleaseIntervalTests(
    "test_cancelled_release_records_each_key_to_shared_sync_bound"))
suite.addTest(BatchReleaseIntervalTests(
    "test_restores_a_preloaded_owner_module_after_fake_xlib_run"))
suite.addTests(loader.loadTestsFromTestCase(OwnerReceiptJoinTests))
suite.addTests(loader.loadTestsFromTestCase(ExplicitKeyUpCancellationTests))
suite.addTests(loader.loadTestsFromTestCase(ActualReleaseCompositionTests))
suite.addTests(loader.loadTestsFromTestCase(ExecutorV13Tests))
suite.addTest(BatchReleaseIntervalTests(
    "test_cancelled_release_records_each_key_to_shared_sync_bound"))
suite.addTests(loader.loadTestsFromTestCase(ExplicitKeyupKeymapTests))
suite.addTests(loader.loadTestsFromTestCase(UnmatchedKeyUpAliasTests))

ROOT = Path(__file__).resolve().parent
stream = io.StringIO()
result = unittest.TextTestRunner(verbosity=2, stream=stream).run(suite)
output = stream.getvalue()
print(output, end="")
(ROOT / "ordered.stdout.txt").write_text(output)
(ROOT / "ordered.exit.txt").write_text("0\n" if result.wasSuccessful() else "1\n")
raise SystemExit(not result.wasSuccessful())
