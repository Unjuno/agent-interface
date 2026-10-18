"""Behavior tests for evidence-grounded optional resume suggestions."""

import importlib.util
import copy
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent


class ResumeSuggestionTests(unittest.TestCase):
    def test_only_one_fresh_publicly_entailed_checkpoint_is_suggested(self):
        self.assertIsNotNone(importlib.util.find_spec("candidate"), "candidate.py is not implemented")
        import candidate

        fixture = json.loads((ROOT / "input.json").read_text(encoding="utf-8"))
        result = candidate.run(fixture)
        rows = {row["case_id"]: row for row in result["rows"]}

        self.assertEqual("open", rows["unique_initial"]["suggestion"]["checkpoint_id"])
        self.assertEqual("configure", rows["unique_after_receipt"]["suggestion"]["checkpoint_id"])
        for case_id in (
            "ambiguous_alternatives", "stale_state", "wrong_window", "changed_task",
            "completed_task", "cancelled_predecessor", "unresolved_effect", "no_contract",
        ):
            self.assertIsNone(rows[case_id]["suggestion"], case_id)

        left = dict(rows["paired_hidden_a"])
        right = dict(rows["paired_hidden_b"])
        left.pop("case_id")
        right.pop("case_id")
        self.assertEqual(left, right)
        for row in result["rows"]:
            self.assertEqual("none", row["authority"])
            self.assertEqual("snapshot_requires_revalidation", row["freshness"])
            if row["suggestion"] is not None:
                self.assertTrue(row["suggestion"]["source_ids"])
                self.assertEqual(row["provenance"]["state_generation"], row["provenance"]["observation_generation"])

    def test_malformed_or_cyclic_checkpoint_graphs_abstain(self):
        self.assertIsNotNone(importlib.util.find_spec("candidate"), "candidate.py is not implemented")
        import candidate

        fixture = json.loads((ROOT / "input.json").read_text(encoding="utf-8"))
        malformed = copy.deepcopy(fixture)
        base = copy.deepcopy(malformed["cases"][0]["public"])
        variants = []

        duplicate = copy.deepcopy(base)
        duplicate["contract"]["checkpoints"] = [{"id": "x", "depends_on": []}, {"id": "x", "depends_on": []}]
        variants.append(duplicate)

        cyclic = copy.deepcopy(base)
        cyclic["contract"]["checkpoints"] = [{"id": "x", "depends_on": ["y"]}, {"id": "y", "depends_on": ["x"]}]
        variants.append(cyclic)

        missing_parent = copy.deepcopy(base)
        missing_parent["contract"]["checkpoints"] = [{"id": "x", "depends_on": ["not-declared"]}]
        variants.append(missing_parent)

        for index, public in enumerate(variants):
            malformed["cases"] = [{"case_id": f"malformed-{index}", "public": public}]
            row = candidate.run(malformed)["rows"][0]
            self.assertIsNone(row["suggestion"])
            self.assertEqual("INVALID_PLAN", row["reason"])


if __name__ == "__main__":
    unittest.main()
