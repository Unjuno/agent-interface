"""Host-only construction tests for the #5139 sampler; no model or Docker use."""

from __future__ import annotations

import unittest

from qwen5139_sampler import CLASSES, COUNTS, row_rank, select_support


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
            class_name = (
                "yield:"
                + ("forbidden", "ambiguous", "stale_scope", "missing_evidence")[(i // 8) % 4]
            )
            template = -1
            field = -1
        else:
            reason = "already_satisfied" if i % 2 else "not_requested"
            class_name = f"no_action:{reason}"
            template = -1
            field = 0
        rows.append(
            {
                "case_id": f"support-{i:04d}",
                "class": class_name,
                "template": template,
                "field": field,
            }
        )
    return [row for row in rows if row["class"] in CLASSES]


class SamplerTests(unittest.TestCase):
    def test_rank_is_order_independent_and_seed_sensitive(self) -> None:
        rows = support_pool()
        selected_a, balanced_a = select_support(rows, "construction-only-manual-probe")
        selected_b, balanced_b = select_support(
            list(reversed(rows)), "construction-only-manual-probe"
        )
        self.assertEqual(selected_a, selected_b)
        self.assertEqual(balanced_a, balanced_b)
        self.assertNotEqual(
            row_rank("construction-only-manual-probe", "set", "support-0000"),
            row_rank("different-probe", "set", "support-0000"),
        )

    def test_arm_counts_and_nested_selection(self) -> None:
        imbalanced, balanced = select_support(
            support_pool(), "construction-only-manual-probe"
        )
        for class_name in CLASSES:
            a = [row["case_id"] for row in imbalanced[class_name]]
            b = [row["case_id"] for row in balanced[class_name]]
            self.assertEqual(len(a), COUNTS["imbalanced"][class_name])
            self.assertEqual(len(b), COUNTS["balanced"][class_name])
            smaller, larger = (a, b) if len(a) <= len(b) else (b, a)
            self.assertTrue(set(smaller).issubset(larger), class_name)
            if len(a) == len(b):
                self.assertEqual(a, b, class_name)

    def test_removes_deterministic_set_template_prefix(self) -> None:
        rows = support_pool()
        old_prefix = [row for row in rows if row["class"] == "set"][:4]
        imbalanced, balanced = select_support(
            rows, "construction-only-manual-probe"
        )
        self.assertEqual(len({row["template"] for row in old_prefix}), 1)
        self.assertEqual(
            len({row["template"] for row in balanced["set"]}), 4
        )
        self.assertEqual(
            len({row["template"] for row in imbalanced["set"]}), 4
        )

    def test_rejects_duplicate_ids_and_short_class(self) -> None:
        rows = support_pool()
        with self.assertRaisesRegex(ValueError, "duplicate_case_id"):
            select_support(rows + [rows[0]], "construction-only-manual-probe")
        short = [row for row in rows if row["class"] != "set"]
        with self.assertRaisesRegex(ValueError, "missing_classes:set"):
            select_support(short, "construction-only-manual-probe")


if __name__ == "__main__":
    unittest.main()

