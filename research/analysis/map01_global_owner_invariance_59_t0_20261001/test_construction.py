import json
import unittest
from pathlib import Path

CASES = json.loads((Path(__file__).parent / "cases.json").read_text(encoding="utf-8"))


class FrozenMatrixTests(unittest.TestCase):
    def test_full_event_head_factorial_is_balanced(self):
        matrix = CASES["matrix"]
        self.assertEqual(8, len(matrix))
        self.assertEqual({"push", "workflow_dispatch"}, {c["current_event"] for c in matrix})
        self.assertEqual({"push", "workflow_dispatch"}, {c["prior_event"] for c in matrix})
        self.assertEqual({"same", "different"}, {c["prior_head"] for c in matrix})
        self.assertEqual(8, len({c["case_id"] for c in matrix}))

    def test_each_event_and_sha_cell_has_one_same_and_one_cross_event_case(self):
        for current in ("push", "workflow_dispatch"):
            for prior_head in ("same", "different"):
                matching = [c for c in CASES["matrix"] if c["current_event"] == current and c["prior_head"] == prior_head]
                self.assertEqual(2, len(matching))
                self.assertEqual({"same", "different"}, {"same" if c["prior_event"] == current else "different" for c in matching})

    def test_controls_are_frozen(self):
        self.assertEqual(["first_run_no_prior_owner", "truncated_event_scoped_view"], CASES["controls"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
