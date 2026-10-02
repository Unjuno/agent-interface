"""Host construction tests; no model, optimizer, network or application state."""

from __future__ import annotations

import copy
import unittest

from audit_support import audit
from build_support import construct


class StratifiedFeasibilityTests(unittest.TestCase):
    def test_constructed_arms_match_template_and_field_marginals(self) -> None:
        raw = construct()
        self.assertEqual(audit(raw), [])
        self.assertEqual(raw["descriptor"]["large_template_counts"], {"0": 4, "1": 4, "2": 4, "3": 4})
        self.assertEqual(raw["descriptor"]["small_template_counts"], {"0": 1, "1": 1, "2": 1, "3": 1})
        self.assertEqual(set(raw["descriptor"]["large_field_counts"].values()), {4})
        self.assertEqual(set(raw["descriptor"]["small_field_counts"].values()), {1})

    def test_rejects_broken_nested_selection(self) -> None:
        raw = construct()
        raw["small"][0] = copy.deepcopy(raw["small"][0])
        raw["small"][0]["case_id"] = "not-in-large-or-pool"
        self.assertIn("arm_not_subset_of_pool:small", audit(raw))
        self.assertIn("small_not_nested_in_large", audit(raw))

    def test_rejects_changed_template_and_field_marginals(self) -> None:
        raw = construct()
        raw["small"][0]["template"] = 99
        raw["small"][1]["field"] = "unknown"
        errors = audit(raw)
        self.assertIn("template_marginals:small", errors)
        self.assertIn("field_marginals:small", errors)

    def test_rejects_duplicate_pool_ids(self) -> None:
        raw = construct()
        raw["pool"].append(copy.deepcopy(raw["pool"][0]))
        self.assertIn("duplicate_pool_id", audit(raw))


if __name__ == "__main__":
    unittest.main()
