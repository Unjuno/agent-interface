import copy
import json
import unittest
from pathlib import Path

from candidate import run


ROOT = Path(__file__).parent


def load_visible():
    return json.loads((ROOT / "visible.json").read_text(encoding="utf-8"))


class CandidateRowsTests(unittest.TestCase):
    def test_age_only_pair_has_identical_visible_rows(self):
        visible = load_visible()
        raw = run(visible)
        stable = [r for r in raw["rows"] if r["case_id"] == "age_tie_stable"]
        changed = [r for r in raw["rows"] if r["case_id"] == "age_tie_changed"]
        self.assertEqual(
            [{k: v for k, v in r.items() if k != "case_id"} for r in stable],
            [{k: v for k, v in r.items() if k != "case_id"} for r in changed],
        )
        self.assertEqual([3, 4, 5], [r["evidence_age"] for r in stable if r["opportunity_open"]])

    def test_noncomparable_clock_does_not_emit_numeric_age(self):
        visible = load_visible()
        raw = run(visible)
        rows = [r for r in raw["rows"] if r["case_id"] == "unknown_truth_clock"]
        self.assertTrue(rows)
        self.assertTrue(all(r["evidence_age"] is None for r in rows))

    def test_candidate_does_not_receive_audit_only_safety_event(self):
        visible = load_visible()
        raw = run(visible)
        row = next(r for r in raw["rows"] if r["case_id"] == "hard_safety_control")
        self.assertEqual("A", row["selected_action"])
        self.assertIn(row["selected_action"], row["admissible_actions"])


if __name__ == "__main__":
    unittest.main()
