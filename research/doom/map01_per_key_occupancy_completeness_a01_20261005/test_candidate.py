import copy
import json
import unittest
from pathlib import Path

from candidate import summarize_complete
from ledger import summarize


HERE = Path(__file__).resolve().parent


class ExpectedKeyInventoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.events = json.loads((HERE / "raw.json").read_text(encoding="utf-8"))["events"]

    def test_complete_inventory_preserves_bounds(self):
        result = summarize_complete(self.events)
        self.assertEqual("BOUNDED", result["status"])
        self.assertEqual({"SPACE", "W"}, {row["key"] for row in result["intervals"]})
        self.assertEqual({"SPACE": (32, 50), "W": (70, 90)},
                         {row["key"]: (row["lower_ns"], row["upper_ns"])
                          for row in result["intervals"]})

    def test_retained_ledger_accepts_dropped_key_row(self):
        omitted = [copy.deepcopy(r) for r in self.events
                   if not (r.get("kind") == "key_interval" and r.get("key") == "SPACE")]
        self.assertEqual("BOUNDED", summarize(omitted)["status"])
        self.assertEqual(["W"], [r["key"] for r in summarize(omitted)["intervals"]])

    def test_completeness_wrapper_rejects_dropped_key_row(self):
        omitted = [copy.deepcopy(r) for r in self.events
                   if not (r.get("kind") == "key_interval" and r.get("key") == "SPACE")]
        result = summarize_complete(omitted)
        self.assertEqual("UNKNOWN", result["status"])
        self.assertEqual(["expected_key_inventory_mismatch"], result["reasons"])
        self.assertEqual([], result["intervals"])

    def test_invalid_expected_inventory_fails_closed(self):
        result = summarize_complete(self.events, ("W", "W"))
        self.assertEqual("UNKNOWN", result["status"])
        self.assertEqual(["invalid_expected_key_inventory"], result["reasons"])


if __name__ == "__main__":
    unittest.main()
