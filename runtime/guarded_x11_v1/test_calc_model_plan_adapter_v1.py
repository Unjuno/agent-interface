import copy
import json
import unittest
from pathlib import Path

from runtime.guarded_x11_v1.calc_model_plan_adapter_v1 import (
    adapt_calc_model_plan,
)


class CalcModelPlanAdapterTests(unittest.TestCase):
    def setUp(self):
        self.answer = {
            "cells_blank": True,
            "confidence": 0.99,
            "proposed_actions": ["enter_731_in_A1", "enter_864_in_A2", "save"],
            "selected_cell": "A1",
            "visible_sheet": "Sheet1",
            "visual_note": (
                "Sheet1 is visible; A1 is selected and the visible worksheet "
                "cells are blank."
            ),
        }

    def test_saved_r93_answer_maps_to_fixed_task_values(self):
        evidence = Path(__file__).parents[2] / "research" / "integration" / (
            "issue57_model_usage_preflight_20261104_r93") / "r93-a01" / (
            "worker-result.json")
        if evidence.is_file():
            saved = json.loads(evidence.read_text(encoding="utf-8"))
            self.assertEqual(saved["status"], "completed")
            self.assertTrue(saved["answer_eligible"])
            self.assertEqual(saved["usage"]["last"]["inputTokens"], 11938)
            self.assertEqual(saved["usage"]["last"]["outputTokens"], 76)
            answer = saved["answer"]
        else:
            # Keep the unit test runnable from a clean checkout without the
            # separately retained, untracked historical evidence packet.
            answer = self.answer
        self.assertEqual(adapt_calc_model_plan(answer), {"A1": "731", "A2": "864"})

    def test_rejects_unsafe_or_ambiguous_plan_variants(self):
        mutations = (
            lambda value: value.update(confidence=0.89),
            lambda value: value.update(confidence=True),
            lambda value: value.update(confidence=10 ** 1000),
            lambda value: value.update(confidence=float("nan")),
            lambda value: value.update(visible_sheet="unknown"),
            lambda value: value.update(selected_cell="A2"),
            lambda value: value.update(cells_blank=False),
            lambda value: value.update(proposed_actions=[
                "enter_864_in_A2", "enter_731_in_A1", "save"]),
            lambda value: value.update(proposed_actions=[
                "enter_731_in_A1", "enter_864_in_A2", "save", "abstain"]),
            lambda value: value.update(extra="untrusted field"),
        )
        for mutate in mutations:
            candidate = copy.deepcopy(self.answer)
            mutate(candidate)
            with self.subTest(candidate=candidate), self.assertRaises(ValueError):
                adapt_calc_model_plan(candidate)

    def test_note_is_bounded_and_never_parsed_as_task_values(self):
        answer = copy.deepcopy(self.answer)
        answer["visual_note"] = "731 in A1 and 864 in A2. " + "x" * 200
        with self.assertRaises(ValueError):
            adapt_calc_model_plan(answer)
        answer["visual_note"] = "Values differ in prose: 1 and 2."
        self.assertEqual(adapt_calc_model_plan(answer), {"A1": "731", "A2": "864"})


if __name__ == "__main__":
    unittest.main()
