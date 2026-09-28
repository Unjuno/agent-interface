"""Independent support-selection auditor tests; all mutations must fail closed."""

from __future__ import annotations

import copy
import unittest

from audit_sampler import audit_support_selection
from sampler import select_support
from test_sampler import TEST_SEED, support_pool


def dataset_fixture() -> dict[str, object]:
    pool = support_pool()
    imbalanced, balanced = select_support(pool, TEST_SEED)
    return {
        "seed": TEST_SEED,
        "support_pool": pool,
        "supports": {
            "imbalanced": [
                row for class_name in (
                    "set", "save", "toggle", "yield:forbidden",
                    "yield:ambiguous", "yield:stale_scope",
                    "yield:missing_evidence", "no_action:already_satisfied",
                ) for row in imbalanced[class_name]
            ],
            "balanced": [
                row for class_name in (
                    "set", "save", "toggle", "yield:forbidden",
                    "yield:ambiguous", "yield:stale_scope",
                    "yield:missing_evidence", "no_action:already_satisfied",
                ) for row in balanced[class_name]
            ],
        },
    }


class IndependentSamplerAuditTests(unittest.TestCase):
    def test_candidate_rows_reconstruct_without_auditor_importing_sampler(self) -> None:
        self.assertEqual(audit_support_selection(dataset_fixture()), [])

    def test_rejects_changed_seed(self) -> None:
        data = dataset_fixture()
        data["seed"] = TEST_SEED + 1
        self.assertIn("selected_id_order:balanced", audit_support_selection(data))

    def test_rejects_reordered_arm(self) -> None:
        data = dataset_fixture()
        data["supports"]["balanced"].reverse()
        self.assertIn("selected_id_order:balanced", audit_support_selection(data))

    def test_rejects_substituted_case(self) -> None:
        data = dataset_fixture()
        data["supports"]["balanced"][0] = data["support_pool"][-1]
        errors = audit_support_selection(data)
        self.assertIn("selected_id_order:balanced", errors)
        self.assertIn("support_counts:balanced", errors)

    def test_rejects_mutated_selected_row(self) -> None:
        data = dataset_fixture()
        data["supports"]["balanced"][0] = copy.deepcopy(data["supports"]["balanced"][0])
        data["supports"]["balanced"][0]["template"] = 999
        self.assertIn("selected_row_content:balanced", audit_support_selection(data))

    def test_rejects_duplicate_pool_id(self) -> None:
        data = dataset_fixture()
        data["support_pool"].append(copy.deepcopy(data["support_pool"][0]))
        self.assertTrue(
            any(error.startswith("duplicate_support_case_id:") for error in audit_support_selection(data))
        )


if __name__ == "__main__":
    unittest.main()

