"""Independent support-selection auditor tests; all mutations must fail closed."""

from __future__ import annotations

import copy
import hashlib
import unittest

from audit_sampler import audit_support_selection


TEST_SEED = 1
CLASSES = (
    "set", "save", "toggle", "yield:forbidden", "yield:ambiguous",
    "yield:stale_scope", "yield:missing_evidence", "no_action:already_satisfied",
)
COUNTS = {
    "imbalanced": (16, 4, 4, 1, 1, 1, 1, 4),
    "balanced": (4, 4, 4, 4, 4, 4, 4, 4),
}


def support_pool() -> list[dict[str, object]]:
    rows = []
    for i in range(128):
        kind = i % 8
        if kind <= 3:
            class_name = "set"
            template = (i // 8) % 4
            field = (i // 8 + kind) % 4
        elif kind == 4:
            class_name = "save"
            template = (i // 8) % 4
            field = (i // 8) % 4
        elif kind == 5:
            class_name = "toggle"
            template = (i // 8) % 4
            field = 0
        elif kind == 6:
            class_name = "yield:" + (
                "forbidden", "ambiguous", "stale_scope", "missing_evidence"
            )[(i // 8) % 4]
            template = -1
            field = -1
        else:
            class_name = "no_action:already_satisfied" if i % 2 else "no_action:not_requested"
            template = -1
            field = 0
        if class_name in CLASSES:
            rows.append({"case_id": f"support-{i:04d}", "class": class_name,
                         "template": template, "field": field})
    return rows


def independent_selection(pool: list[dict[str, object]], arm: str) -> list[dict[str, object]]:
    selected = []
    for class_name, count in zip(CLASSES, COUNTS[arm]):
        candidates = [row for row in pool if row["class"] == class_name]
        candidates.sort(key=lambda row: (
            hashlib.sha256(
                b"support-row-rank-v1\n" + str(TEST_SEED).encode("ascii") + b"\n"
                + class_name.encode("utf-8") + b"\n" + str(row["case_id"]).encode("utf-8")
            ).digest(),
            str(row["case_id"]).encode("utf-8"),
        ))
        selected.extend(candidates[:count])
    return selected


def dataset_fixture() -> dict[str, object]:
    pool = support_pool()
    return {
        "seed": TEST_SEED,
        "support_pool": pool,
        "supports": {
            "imbalanced": independent_selection(pool, "imbalanced"),
            "balanced": independent_selection(pool, "balanced"),
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

