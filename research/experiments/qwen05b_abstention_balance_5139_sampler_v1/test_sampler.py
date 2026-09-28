"""Host-only construction tests for the #5139 sampler; no model or Docker use."""

from __future__ import annotations

import unittest
import hashlib

from sampler import CLASSES, COUNTS, row_rank, select_support


TEST_SEED = 1


def independent_rank(seed: int, class_name: str, case_id: str) -> bytes:
    """Test oracle, deliberately reconstructed without candidate row_rank."""
    message = b"support-row-rank-v1\n" + str(seed).encode("ascii")
    message += b"\n" + class_name.encode("utf-8") + b"\n" + case_id.encode("utf-8")
    return hashlib.sha256(message).digest()


def independent_selected_ids(rows: list[dict[str, object]], seed: int) -> dict[str, dict[str, list[str]]]:
    result: dict[str, dict[str, list[str]]] = {"imbalanced": {}, "balanced": {}}
    for class_name in CLASSES:
        candidates = [row for row in rows if row["class"] == class_name]
        candidates.sort(
            key=lambda row: (
                independent_rank(seed, class_name, str(row["case_id"])),
                str(row["case_id"]).encode("utf-8"),
            )
        )
        for arm in ("imbalanced", "balanced"):
            total = COUNTS[arm][class_name]
            result[arm][class_name] = [
                str(row["case_id"]) for row in candidates[:total]
            ]
    return result


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
        selected_a, balanced_a = select_support(rows, TEST_SEED)
        selected_b, balanced_b = select_support(
            list(reversed(rows)), TEST_SEED
        )
        self.assertEqual(selected_a, selected_b)
        self.assertEqual(balanced_a, balanced_b)
        self.assertNotEqual(
            row_rank(TEST_SEED, "set", "support-0000"),
            row_rank(TEST_SEED + 1, "set", "support-0000"),
        )

    def test_candidate_selection_matches_independent_oracle(self) -> None:
        rows = support_pool()
        imbalanced, balanced = select_support(rows, TEST_SEED)
        expected = independent_selected_ids(rows, TEST_SEED)
        self.assertEqual(
            {name: [r["case_id"] for r in values] for name, values in imbalanced.items()},
            expected["imbalanced"],
        )
        self.assertEqual(
            {name: [r["case_id"] for r in values] for name, values in balanced.items()},
            expected["balanced"],
        )

    def test_arm_counts_and_nested_selection(self) -> None:
        imbalanced, balanced = select_support(
            support_pool(), TEST_SEED
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

    def test_ranked_selection_escapes_the_fixed_set_prefix(self) -> None:
        rows = support_pool()
        old_prefix = [row for row in rows if row["class"] == "set"][:4]
        imbalanced, balanced = select_support(
            rows, TEST_SEED
        )
        self.assertEqual(len({row["template"] for row in old_prefix}), 1)
        old_ids = [row["case_id"] for row in old_prefix]
        ranked_ids = [row["case_id"] for row in balanced["set"]]
        self.assertNotEqual(ranked_ids, old_ids)
        self.assertGreater(len({row["template"] for row in balanced["set"]}), 1)

    def test_rejects_duplicate_ids_and_short_class(self) -> None:
        rows = support_pool()
        with self.assertRaisesRegex(ValueError, "duplicate_case_id"):
            select_support(rows + [rows[0]], TEST_SEED)
        short = [row for row in rows if row["class"] != "set"]
        with self.assertRaisesRegex(ValueError, "missing_classes:set"):
            select_support(short, TEST_SEED)

    def test_rejects_noncanonical_seed_types(self) -> None:
        with self.assertRaisesRegex(ValueError, "seed_must_be_positive_integer"):
            row_rank(True, "set", "support-0000")
        with self.assertRaisesRegex(ValueError, "seed_must_be_positive_integer"):
            row_rank("0", "set", "support-0000")  # type: ignore[arg-type]
        with self.assertRaisesRegex(ValueError, "seed_must_be_positive_integer"):
            row_rank(0, "set", "support-0000")


if __name__ == "__main__":
    unittest.main()

