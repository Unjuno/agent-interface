"""Matched-model/effort contract tests for the Issue #57 evaluator."""

from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "research" / "live_control"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from integrated_efficiency_protocol_v1 import evaluate  # noqa: E402
from probe_integrated_efficiency_protocol_v1 import trace  # noqa: E402
from audit_model_effort_guard import audit  # noqa: E402


ARMS = ("plain", "ephemeral", "persistent")


class ModelEffortGuardTests(unittest.TestCase):
    def test_matched_positive_trace_remains_retain(self):
        self.assertEqual(evaluate(trace())["disposition"], "RETAIN")

    def test_each_task_arm_rejects_model_mismatch(self):
        for arm in ARMS:
            with self.subTest(arm=arm):
                candidate = copy.deepcopy(trace())
                candidate["arms"][arm][0]["model_calls"][0]["requested_model"] = "other-model"
                with self.assertRaisesRegex(ValueError, "model/effort mismatch"):
                    evaluate(candidate)

    def test_each_task_arm_rejects_effort_mismatch(self):
        for arm in ARMS:
            with self.subTest(arm=arm):
                candidate = copy.deepcopy(trace())
                candidate["arms"][arm][0]["model_calls"][0]["requested_effort"] = "high"
                with self.assertRaisesRegex(ValueError, "model/effort mismatch"):
                    evaluate(candidate)

    def test_each_preflight_rejects_model_mismatch(self):
        for arm in ARMS:
            with self.subTest(arm=arm):
                candidate = copy.deepcopy(trace())
                candidate["preflight_calls"][arm]["requested_model"] = "other-model"
                with self.assertRaisesRegex(ValueError, "model/effort mismatch"):
                    evaluate(candidate)

    def test_each_preflight_rejects_effort_mismatch(self):
        for arm in ARMS:
            with self.subTest(arm=arm):
                candidate = copy.deepcopy(trace())
                candidate["preflight_calls"][arm]["requested_effort"] = "high"
                with self.assertRaisesRegex(ValueError, "model/effort mismatch"):
                    evaluate(candidate)

    def test_preflight_to_task_call_must_match(self):
        candidate = copy.deepcopy(trace())
        candidate["preflight_calls"]["plain"]["requested_effort"] = "high"
        with self.assertRaisesRegex(ValueError, "model/effort mismatch"):
            evaluate(candidate)

    def test_zero_task_call_reuse_rows_remain_valid(self):
        valid = trace()
        self.assertEqual(valid["arms"]["persistent"][1]["model_calls"], [])
        self.assertEqual(evaluate(valid)["disposition"], "RETAIN")

    def test_independent_oracle_matches_baseline_and_rejects_mutation(self):
        valid = trace()
        self.assertEqual(audit(valid)["decision"], "PASS_MATCHED_MODEL_EFFORT")
        changed = copy.deepcopy(valid)
        changed["arms"]["persistent"][0]["model_calls"][0][
            "requested_model"] = "other-model"
        self.assertEqual(audit(changed)["decision"], "FAIL_MODEL_EFFORT_MISMATCH")


if __name__ == "__main__":
    unittest.main()
