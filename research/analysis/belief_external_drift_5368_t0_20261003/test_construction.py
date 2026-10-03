"""Pre-freeze fixture and source-construction checks; never invokes candidate."""
from __future__ import annotations

import ast
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent


class ConstructionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.fixture = json.loads((ROOT / "fixture.json").read_text(encoding="utf-8"))
        cls.cases = cls.fixture["cases"]

    def test_fixed_case_inventory_and_unique_ids(self) -> None:
        self.assertEqual(self.fixture["schema_version"], 1)
        self.assertEqual(len(self.cases), 9)
        ids = [case["id"] for case in self.cases]
        self.assertEqual(len(ids), len(set(ids)))

    def test_every_trace_has_a_consistent_endpoint(self) -> None:
        for case in self.cases:
            trace = case["truth"]["actual_trace"]
            self.assertEqual(len(trace), case["input"]["elapsed_steps"] + 1, case["id"])
            self.assertEqual(trace[0], case["input"]["initial_belief"][0], case["id"])
            self.assertEqual(trace[-1], case["truth"]["actual_state"], case["id"])

    def test_all_scenario_categories_are_predeclared(self) -> None:
        expected = {
            "complete_no_disturbance",
            "hidden_redirect_without_observation",
            "redirect_then_fresh_safe_observation",
            "redirect_then_fresh_unsafe_observation",
            "stale_generation_observation_ignored",
            "unknown_transition_alphabet",
            "out_of_support_state_possible",
            "fresh_observation_contradicts_complete_model",
            "two_step_reachability",
        }
        self.assertEqual({case["id"] for case in self.cases}, expected)

    def test_declared_complete_traces_are_representable_except_planted_contradiction(self) -> None:
        for case in self.cases:
            item = case["input"]
            if item["transition_complete"] is not True:
                continue
            relation = item["transition_relation"]
            trace = case["truth"]["actual_trace"]
            representable = all(left in relation and right in relation[left] for left, right in zip(trace, trace[1:]))
            if case["id"] == "fresh_observation_contradicts_complete_model":
                self.assertFalse(representable, case["id"])
            else:
                self.assertTrue(representable, case["id"])

    def test_formal_outputs_absent_before_freeze(self) -> None:
        for name in ("formal_raw.jsonl", "sticky_baseline.jsonl", "age_baseline.jsonl", "audit.json"):
            self.assertFalse((ROOT / name).exists(), name)

    def test_python_sources_parse_without_importing_or_running_them(self) -> None:
        for name in ("candidate.py", "runner.py", "audit.py"):
            ast.parse((ROOT / name).read_text(encoding="utf-8"), filename=name)


if __name__ == "__main__":
    unittest.main()
