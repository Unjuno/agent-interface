import json
import unittest
from pathlib import Path

import independent_audit_v2


ROOT = Path(__file__).resolve().parent


def swapped_labels(raw):
    for implementation in ("baseline", "candidate"):
        cases = raw["interval_sweep"][implementation]["cases"]
        was_ordered = cases[4]
        was_unordered = cases[15]
        was_ordered["expected_ordered"] = False
        was_ordered["status"] = "adapter_edge_receipt_incomplete"
        was_ordered["down_edge_interval_ns"] = None
        was_ordered["up_edge_interval_ns"] = None
        was_unordered["expected_ordered"] = True
        was_unordered["status"] = "adapter_edge_brackets_paired"
        was_unordered["down_edge_interval_ns"] = was_unordered["down"]
        was_unordered["up_edge_interval_ns"] = was_unordered["up"]
    return raw


class RawIntervalIndependenceTests(unittest.TestCase):
    def raw(self):
        return json.loads((ROOT / "frozen" / "raw" / "A01.json").read_text(encoding="utf-8"))

    def test_saved_sweep_is_consistent_with_interval_chronology(self):
        result = independent_audit_v2.audit_raw(self.raw())
        self.assertEqual([], result["errors"])
        self.assertEqual({"baseline": (15, 85), "candidate": (15, 85)}, result["counts"])

    def test_reclassifying_a_true_and_false_pair_cannot_hide_against_label_counts(self):
        result = independent_audit_v2.audit_raw(swapped_labels(self.raw()))
        self.assertEqual({"baseline": (15, 85), "candidate": (15, 85)}, result["counts"])
        self.assertEqual(4, sum("expected_ordered_mismatch" in error for error in result["errors"]))


if __name__ == "__main__":
    unittest.main()
