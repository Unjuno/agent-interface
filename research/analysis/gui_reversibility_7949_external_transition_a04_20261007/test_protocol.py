import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))
import candidate


class A04Tests(unittest.TestCase):
    def test_external_write_invalidates_then_recertifies(self):
        model = json.loads((ROOT / "model.json").read_text(encoding="utf-8"))
        rows = {r["id"]: r for r in candidate.run(model)}
        self.assertEqual(rows["pre_interference"]["label"], "UNIVERSALLY_UNIFORM")
        self.assertEqual(rows["stale_then_refreshed"]["stale"]["label"], "UNKNOWN_STALE_CERTIFICATE")
        fresh = rows["stale_then_refreshed"]["refreshed"]
        self.assertEqual((fresh["label"], fresh["final"]), ("UNIVERSALLY_UNIFORM", "010"))
        self.assertTrue(rows["stale_then_refreshed"]["external_bit_preserved"])
        self.assertEqual(rows["journal_gap"]["label"], "UNKNOWN_EVENT_CHAIN")


if __name__ == "__main__":
    unittest.main()
