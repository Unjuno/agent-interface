import json
import unittest
from pathlib import Path


class FreezeSchemaTests(unittest.TestCase):
    def test_current_allocation_freeze_has_complete_provenance(self):
        source = Path(__file__).parent
        freeze = json.loads((source / "FREEZE.json").read_text(encoding="utf-8"))
        self.assertEqual(freeze["issue"], 5139)
        self.assertEqual(freeze["allocation"], "qwen5139-support-balance-currentmain-eddcf7a4-20260930-02")
        self.assertEqual(freeze["current_main_sha"], "eddcf7a47c1f3c47165288037e66f66da0c3138a")
        self.assertEqual(set(freeze["seeds"]), {"formal_seed", "support_seed", "heldout_seed"})
        self.assertEqual(len(set(freeze["seeds"].values())), 3)
        self.assertEqual(sum(freeze["data"]["support_counts"]["balanced"].values()), 32)
        self.assertEqual(len(freeze["data"]["classes"]), 8)
        self.assertEqual(freeze["data"]["heldout_rows"], 64)
        self.assertEqual(freeze["data"]["heldout_pool_rows"], 256)
        self.assertIn("--preflight-only", freeze["commands"]["preflight_only"])
        self.assertIn(freeze["image"]["digest"], freeze["commands"]["formal"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
