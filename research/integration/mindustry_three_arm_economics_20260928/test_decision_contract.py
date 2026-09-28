"""Host-only boundary tests for the frozen #1679 Mindustry decision rule.

All traces here are synthetic contract fixtures. They do not call a model,
launch Mindustry, or produce evidence about live task economics.
"""

from __future__ import annotations

import copy
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parent
REPOSITORY = next(parent for parent in ROOT.parents if (parent / ".git").exists())
LIVE = REPOSITORY / "research" / "live_control"
sys.path.insert(0, str(LIVE))

import integrated_efficiency_protocol_v1 as protocol  # noqa: E402
import probe_integrated_efficiency_protocol_v1 as probe  # noqa: E402


class MindustryDecisionContractTests(unittest.TestCase):
    def setUp(self):
        self.trace = probe.trace()

    def test_reference_trace_satisfies_frozen_rule(self):
        result = protocol.evaluate(self.trace)
        self.assertEqual(result["disposition"], "RETAIN")
        self.assertEqual(result["observed_break_even_task"], 2)
        self.assertTrue(result["beats_both_input_tokens_by_task_6"])
        self.assertTrue(result["beats_both_planner_generations_by_task_6"])

    def test_strict_break_even_at_task_four_is_eligible(self):
        candidate = copy.deepcopy(self.trace)
        candidate["arms"]["persistent"][0]["model_calls"][0]["usage"]["input_tokens"] = 32_000
        candidate["arms"]["persistent"][3]["model_calls"][0]["usage"]["input_tokens"] = 3_000
        result = protocol.evaluate(candidate)
        self.assertEqual(result["observed_break_even_task"], 4)
        self.assertEqual(result["disposition"], "RETAIN")

    def test_equality_at_task_four_does_not_count_as_break_even(self):
        candidate = copy.deepcopy(self.trace)
        candidate["arms"]["persistent"][0]["model_calls"][0]["usage"]["input_tokens"] = 32_000
        candidate["arms"]["persistent"][3]["model_calls"][0]["usage"]["input_tokens"] = 4_000
        result = protocol.evaluate(candidate)
        self.assertEqual(result["observed_break_even_task"], 5)
        self.assertEqual(result["disposition"], "REJECT")

    def test_stale_target_admission_blocks_retain(self):
        candidate = copy.deepcopy(self.trace)
        candidate["arms"]["persistent"][3]["old_target_pointer_admissions"] = 1
        result = protocol.evaluate(candidate)
        self.assertEqual(result["disposition"], "REJECT")
        self.assertEqual(result["reason"], "persistent_correctness_repair_or_old_target_gate_failed")

    def test_missing_repair_blocks_retain(self):
        candidate = copy.deepcopy(self.trace)
        candidate["arms"]["persistent"][3]["repair"]["succeeded"] = False
        result = protocol.evaluate(candidate)
        self.assertEqual(result["disposition"], "REJECT")
        self.assertEqual(result["reason"], "persistent_correctness_repair_or_old_target_gate_failed")

    def test_task_call_schedule_mutation_is_rejected(self):
        candidate = copy.deepcopy(self.trace)
        candidate["arms"]["persistent"][1]["model_calls"] = copy.deepcopy(
            candidate["arms"]["plain"][1]["model_calls"])
        with self.assertRaisesRegex(ValueError, "model call count"):
            protocol.evaluate(candidate)


if __name__ == "__main__":
    unittest.main()
