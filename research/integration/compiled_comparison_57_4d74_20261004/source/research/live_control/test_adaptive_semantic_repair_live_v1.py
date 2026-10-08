"""Static preregistration checks before the one live allocation."""
import hashlib
import json
import unittest
from pathlib import Path


HERE = Path(__file__).resolve().parent
PLAN = HERE / "adaptive_semantic_repair_live_v1_prereg.json"


class AdaptiveLivePlanTest(unittest.TestCase):
    def test_plan_is_finite_and_output_is_absent_before_run(self):
        plan = json.loads(PLAN.read_text(encoding="utf-8"))
        self.assertEqual(plan["allocations"], 1)
        self.assertEqual(plan["retry_limit"], 0)
        self.assertEqual(plan["order"], ["local", "model"])
        self.assertEqual(plan["expected_model_calls"], {"local": 1, "model": 2})
        self.assertEqual(plan["model"], {"name": "gpt-5.6-luna", "effort": "low"})
        output = HERE.parent.parent / plan["output"]
        if output.exists():
            self.skipTest("formal output now exists and must never be rerun")

    def test_frozen_sources_match(self):
        plan = json.loads(PLAN.read_text(encoding="utf-8"))
        root = HERE.parent.parent
        for name, expected in plan["source_sha256"].items():
            actual = hashlib.sha256((root / name).read_bytes()).hexdigest()
            self.assertEqual(actual, expected, name)

    def test_required_gates_are_declared(self):
        plan = json.loads(PLAN.read_text(encoding="utf-8"))
        self.assertEqual(set(plan["required_cases"]), {
            "window_resize_local_repair", "button_hover_model_fallback"})
        self.assertIn("independent exact submission", plan["hard_gates"])
        self.assertIn("verified empty release for every input program", plan["hard_gates"])
        self.assertIn("all attempted model calls, images, waits and usage accounted",
                      plan["hard_gates"])


if __name__ == "__main__": unittest.main()
