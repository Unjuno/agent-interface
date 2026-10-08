"""Focused regression for stale partial-action cover reuse."""
import ast
from pathlib import Path
import unittest


HERE = Path(__file__).resolve().parent
SOURCE = HERE / "map01_overlap_controller_v39.py"


def production_reusable_cover():
    """Load the actual selector without importing the controller runtime stack."""
    module = ast.parse(SOURCE.read_text(encoding="utf-8"))
    function = next(node for node in module.body
                    if isinstance(node, ast.FunctionDef) and
                    node.name == "reusable_cover")
    namespace = {}
    isolated = ast.Module(body=[function], type_ignores=[])
    exec(compile(isolated, str(SOURCE), "exec"), namespace)
    return namespace["reusable_cover"]


class ReusableCoverStaleRemainderTests(unittest.TestCase):
    def setUp(self):
        self.reuse = production_reusable_cover()
        self.action = {"state": "active", "next_cover": [
                           {"action": "fire", "extent": "short"}],
                       "next_cover_validity": [{"signal_id": "health",
                           "critical_health_minimum": 35,
                           "maximum_health_loss": 12,
                           "max_source_age_ms": 30000}]}

    def test_partial_stale_rejection_does_not_reuse_remaining_cover(self):
        decision = {"iteration": 1, "model_action_discarded": False,
                    "remaining_action_discarded": True,
                    "executor_preacceptance_rejection": {
                        "reason": "stale_observation"},
                    "action": self.action}

        self.assertEqual(self.reuse([decision]), ([], None, None))

    def test_completed_action_still_reuses_authored_cover(self):
        decision = {"iteration": 2, "model_action_discarded": False,
                    "remaining_action_discarded": False,
                    "action": self.action}

        self.assertEqual(self.reuse([decision]), (
            self.action["next_cover"], self.action["next_cover_validity"][0], 2))

    def test_legacy_completed_record_without_remainder_flag_still_reuses(self):
        decision = {"iteration": 3, "model_action_discarded": False,
                    "action": self.action}

        self.assertEqual(self.reuse([decision]), (
            self.action["next_cover"], self.action["next_cover_validity"][0], 3))


if __name__ == "__main__":
    unittest.main()
