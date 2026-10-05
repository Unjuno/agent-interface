"""A pre-sync release error wakes cancellation monitoring conservatively."""
import importlib.util
from pathlib import Path
import sys
import unittest

LIVE = Path(__file__).resolve().parent
ROOT = LIVE.parents[1]
EXPERIMENT = (ROOT / "research" / "doom" /
              "cancel_key_release_intervals_59_4d74_20261004" /
              "partial_release_failure" / "characterize_sync_failure.py")
sys.path.insert(0, str(LIVE))
sys.path.insert(0, str(EXPERIMENT.parent.parent))
SPEC = importlib.util.spec_from_file_location("partial_release_failure_experiment", EXPERIMENT)
EXPERIMENT_MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(EXPERIMENT_MODULE)


class PartialReleaseFailureTests(unittest.TestCase):
    def test_accepted_then_raised_keyup_publishes_unverified_interruption(self):
        result = EXPERIMENT_MODULE.run_experiment()
        before_close = result["before_close"]
        self.assertTrue(result["injected_request_accepted_then_raised"])
        self.assertEqual(len(before_close["owner_release_records"]), 1)
        self.assertEqual(len(before_close["interruptions"]), 1)
        record = before_close["owner_release_records"][0]
        self.assertEqual(record["reason"], "cancelled")
        self.assertFalse(record["verified"])
        self.assertEqual(record["keys_down"], [ord("A"), ord("W")])
        self.assertEqual(record["key_release_intervals_ns"], [])
        event = result["v13_unverified_publication"]
        self.assertEqual(event["event"], "input_release_unverified")
        self.assertFalse(event["grants_input_authority"])
        later = result["after_close_owner_release_records"]
        self.assertEqual(later[-1]["reason"], "close")
        self.assertTrue(later[-1]["verified"])

    def test_keymap_verification_error_retains_sync_bounds_but_fails_closed(self):
        result = EXPERIMENT_MODULE.run_experiment(failure_phase="verify")
        record = result["before_close"]["owner_release_records"][0]
        self.assertEqual(record["release_error"], "RuntimeError('injected keymap verification failure')")
        self.assertFalse(record["verified"])
        self.assertEqual(record["keys_down"], [ord("A"), ord("W")])
        self.assertEqual(len(record["key_release_intervals_ns"]), 2)
        self.assertEqual(result["v13_unverified_publication"]["event"],
                         "input_release_unverified")
        self.assertFalse(result["v13_unverified_publication"]["grants_input_authority"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
