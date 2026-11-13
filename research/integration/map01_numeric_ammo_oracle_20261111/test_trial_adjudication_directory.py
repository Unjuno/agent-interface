import json
import tempfile
import unittest
from pathlib import Path

from trial_adjudication import adjudicate_retained_trial_directory


class RetainedTrialDirectoryTests(unittest.TestCase):
    def test_missing_task_effect_receipts_are_unknown_not_exception_or_success(self):
        with tempfile.TemporaryDirectory() as directory:
            trial = Path(directory)
            (trial / "action-submission.json").write_text(json.dumps({
                "program": {"authority": {"expires_at_ns": 100}}}),
                encoding="utf-8")
            (trial / "verified-task-effect.json").write_text(json.dumps({
                "call_id": "call-1", "task_success": True,
                "task_effect": {"status": "verified"}}), encoding="utf-8")
            (trial / "expiry-boundary-key-samples.json").write_text(json.dumps({
                "clock": "time.perf_counter_ns",
                "lease_clock": "time.monotonic_ns",
                "samples": [{"before_ns": 90, "after_ns": 91,
                    "w_key_down": True}],
                "sample_count": 1, "max_observed_gap_ns": 0,
                "sample_limit_reached": False, "read_error_type": None,
            }), encoding="utf-8")
            result = adjudicate_retained_trial_directory(trial,
                expected_call_id="call-1")

        self.assertEqual(result["status"], "not_verified")
        self.assertEqual(result["artifacts"]["oracle_receipt"], "missing")
        self.assertEqual(result["artifacts"]["ammo_transition"], "missing")
        self.assertFalse(result["checks"]["exact_call_task_effect"])
        self.assertIsNone(result["task_success"])
        self.assertIsNone(result["terminal_w_down"])

    def test_missing_required_sampler_returns_bounded_unknown(self):
        with tempfile.TemporaryDirectory() as directory:
            trial = Path(directory)
            result = adjudicate_retained_trial_directory(trial,
                expected_call_id="call-1")

        self.assertEqual(result["status"], "not_verified")
        self.assertEqual(result["reason"], "required_artifact_missing_or_invalid")
        self.assertIsNone(result["task_success"])


if __name__ == "__main__":
    unittest.main()
