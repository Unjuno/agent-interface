import unittest
import json
import sys
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from research.live_control.matched_semantic_repair_live_v3 import noncompletion_summary
from research.live_control.semantic_grounding_admission_v1 import admit
from research.live_control.semantic_repair_model_v2 import classify
from research.live_control.scoped_target_handle_v1 import TargetHandleStore
from research.live_control.post_model_target_revalidation_v1 import receipt


class MatchedSemanticRepairV3Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        outcome = classify(ROOT / "results/matched-semantic-repair-live-01/arm-01-local/initial-model")
        cls.admission = admit(outcome)

    def arm(self, stage):
        value = {"status": "TASK_DEFERRED", "passed": False,
                 "comparison_eligible": False, "retry_count": 0}
        value[stage] = self.admission
        return value

    def test_initial_capacity_stops_before_comparison(self):
        result = noncompletion_summary(self.arm("initial_admission"))
        self.assertEqual(result["status"], "DEFERRED")
        self.assertEqual(result["stage"], "initial_grounding")
        self.assertFalse(result["comparison_eligible"])
        self.assertFalse(result["grants_input_authority"])

    def test_later_capacity_is_not_counted_as_sample(self):
        result = noncompletion_summary(self.arm("reacquisition_admission"))
        self.assertEqual(result["stage"], "reacquisition")
        self.assertFalse(result["comparison_eligible"])
        self.assertFalse(result["grants_semantic_authority"])

    def test_noncompleted_arm_cannot_claim_comparison_eligibility(self):
        arm = self.arm("initial_admission")
        arm["comparison_eligible"] = True
        with self.assertRaisesRegex(ValueError, "typed noncompletion"):
            noncompletion_summary(arm)

    def test_post_model_current_observation_revalidates_retained_patch(self):
        arm = ROOT / "results/matched-semantic-repair-live-02/arm-02-model"
        report = json.loads((arm / "report.json").read_text(encoding="utf-8"))
        events = json.loads((arm / "events.json").read_text(encoding="utf-8"))
        source = next(row for row in events
                      if row.get("event") == "observation"
                      and row.get("id") == "matched-repair-resized")
        point = report["reacquisition_outcome"]["result"]["grounding"]["submit_point"]
        box = [point[0]-20, point[1]-9, 42, 18]
        response_ns = source["capture_ns"] + round(
            report["reacquisition_outcome"]["caller_elapsed_ms"]*1_000_000)
        current = {**source, "sequence": source["sequence"]+1,
                   "capture_ns": response_ns+1_000_000}
        with Image.open(arm / Path(source["image"]).name) as opened:
            image = opened.convert("RGB")
        store = TargetHandleStore("post-model", lambda: "save")
        mint = store.mint("save_form", "window_content", box, source, image,
            response_ns, ttl_ms=60000, freshness_ms=3000, search_radius=0,
            allowed_transformations=("window_translation",))
        resolved = store.resolve_point(mint["handle"], [20, 9], current, image,
                                       current["capture_ns"]+1_000_000)
        revalidation = receipt(mint, resolved, source, current,
                               report["reacquisition_outcome"]["result"]["call_id"])
        self.assertTrue(resolved["eligible"])
        self.assertEqual(resolved["status"], "VALID")
        self.assertEqual(resolved["point"], point)
        self.assertEqual(resolved["patch_sha256"], mint["patch_sha256"])
        self.assertEqual(revalidation["status"], "CURRENT_PATCH_MATCH_NO_AUTHORITY")
        self.assertEqual(revalidation["model_source_sequence"], source["sequence"])
        self.assertEqual(revalidation["current_sequence"], current["sequence"])


if __name__ == "__main__":
    unittest.main()
