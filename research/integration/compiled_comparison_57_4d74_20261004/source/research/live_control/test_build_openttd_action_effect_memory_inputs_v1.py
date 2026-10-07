import json
import unittest
from pathlib import Path


HERE = Path(__file__).resolve().parent
OUT = HERE / "results/openttd-action-effect-memory-inputs-01"


class TestDerivedInputs(unittest.TestCase):
    def test_retained_contexts_are_complete_when_present(self):
        if not OUT.exists(): self.skipTest("derived inputs are created before preregistration")
        manifest = json.loads((OUT / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual([row["name"] for row in manifest["contexts"]], ["segment-a-b", "segment-b-c"])
        for row in manifest["contexts"]:
            root = OUT / row["name"]
            for name in ("before.png", "after.png", "current.png", "action-effect-crop.png", "receipt.json"):
                self.assertTrue((root / name).is_file(), name)


if __name__ == "__main__": unittest.main()
