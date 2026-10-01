"""Boundary and retained-trace tests for the v24 one-way invalidation path."""
import json
import sys
import unittest
from pathlib import Path

from PIL import Image


HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "live_control"))

from map01_overlap_controller_v24 import reusable_cover
from policy_invalidation_guard_v1 import PolicyInvalidationGuard


class PolicyInvalidationV24Test(unittest.TestCase):
    def test_discarded_action_cannot_supply_the_next_cover(self):
        active = {"iteration": 4, "action": {
            "state": "active", "next_cover": [{"action": "fire", "extent": "short"}]}}
        self.assertEqual(reusable_cover([active]), (active["action"]["next_cover"], 4))
        active["model_action_discarded"] = True
        self.assertEqual(reusable_cover([active]), ([], None))

    def test_retained_cover_five_invalidates_at_first_health_change(self):
        root = HERE / "results" / "map01-cover-threat-v23-live-02"
        index = json.loads((root / "health-roi-index.json").read_text())
        box = index["box"]
        rows = [row for row in index["rows"] if row["id"] == "cover-5"]
        source = Image.open(root / "frames" / "decision-05.png").convert("RGB")
        guard = PolicyInvalidationGuard({
            "op": "policy_invalidation_guard", "guard_id": "retained-cover-5",
            "source_sequence": 238, "box": box, "metric": "rgb_change",
            "rgb_threshold": 32, "minimum_changed_pixels": 100,
            "max_source_age_ms": 30000, "on_change": "needs_decision",
            "on_unknown": "needs_decision",
        }, source, 238, "retained-binding", rows[0]["capture_ns"] - 1)
        outcomes = []
        for row in rows:
            current = source.copy()
            with Image.open(root / row["retained"]) as roi:
                current.paste(roi.convert("RGB"), (box[0], box[1]))
            outcomes.append((row, guard.evaluate(
                current, row["sequence"], "retained-binding", row["capture_ns"])))
        first = next((pair for pair in outcomes if pair[1]["requires_new_decision"]), None)
        self.assertIsNotNone(first)
        self.assertEqual(first[0]["sequence"], 250)
        self.assertEqual(first[1]["status"], "INVALIDATED")
        self.assertEqual(first[1]["changed_pixels"], 400)
        self.assertAlmostEqual(first[1]["source_age_ms"], 1570.425128, places=6)
        self.assertFalse(first[1]["grants_input_authority"])
        self.assertFalse(first[1]["task_success_verified"])


if __name__ == "__main__":
    unittest.main()
