"""Independent stdlib-only reconstruction of #5139 support selections.

This module intentionally does not import the candidate sampler or protocol.
It verifies support IDs and complete row values against a frozen pool/seed.
"""

from __future__ import annotations

import hashlib
from collections import Counter
from collections.abc import Mapping
from typing import Any


CLASSES = (
    "set",
    "save",
    "toggle",
    "yield:forbidden",
    "yield:ambiguous",
    "yield:stale_scope",
    "yield:missing_evidence",
    "no_action:already_satisfied",
)

COUNTS = {
    "imbalanced": {
        "set": 16,
        "save": 4,
        "toggle": 4,
        "yield:forbidden": 1,
        "yield:ambiguous": 1,
        "yield:stale_scope": 1,
        "yield:missing_evidence": 1,
        "no_action:already_satisfied": 4,
    },
    "balanced": {name: 4 for name in CLASSES},
}


def _rank(seed: int, class_name: str, case_id: str) -> bytes:
    if isinstance(seed, bool) or not isinstance(seed, int) or seed <= 0:
        raise ValueError("seed_must_be_positive_integer")
    payload = (
        b"support-row-rank-v1\n"
        + str(seed).encode("ascii")
        + b"\n"
        + class_name.encode("utf-8")
        + b"\n"
        + case_id.encode("utf-8")
    )
    return hashlib.sha256(payload).digest()


def audit_support_selection(
    dataset: Mapping[str, Any],
) -> list[str]:
    """Return deterministic integrity errors for both support arms."""
    errors: list[str] = []
    # Formal/training randomness is a separate control. Support ordering must
    # bind only to the explicitly frozen support-selection seed.
    seed = dataset.get("support_seed")
    if isinstance(seed, bool) or not isinstance(seed, int) or seed <= 0:
        return ["seed_must_be_positive_integer"]

    pool = dataset.get("support_pool")
    if not isinstance(pool, list):
        return ["support_pool_must_be_list"]

    grouped: dict[str, list[Mapping[str, Any]]] = {
        name: [] for name in CLASSES
    }
    seen: set[str] = set()
    for index, row in enumerate(pool):
        if not isinstance(row, Mapping):
            errors.append(f"support_pool_row_not_object:{index}")
            continue
        class_name = row.get("class")
        case_id = row.get("case_id")
        if class_name not in grouped:
            errors.append(f"unknown_support_class:{index}")
            continue
        if not isinstance(case_id, str) or not case_id:
            errors.append(f"invalid_support_case_id:{index}")
            continue
        if case_id in seen:
            errors.append(f"duplicate_support_case_id:{case_id}")
            continue
        seen.add(case_id)
        grouped[class_name].append(row)

    ranked: dict[str, list[Mapping[str, Any]]] = {}
    for class_name in CLASSES:
        if not grouped[class_name]:
            errors.append(f"missing_support_class:{class_name}")
            continue
        ranked[class_name] = sorted(
            grouped[class_name],
            key=lambda row: (
                _rank(seed, class_name, row["case_id"]),
                row["case_id"].encode("utf-8"),
            ),
        )

    supports = dataset.get("supports")
    if not isinstance(supports, Mapping):
        return errors + ["supports_must_be_object"]
    for arm, class_counts in COUNTS.items():
        arm_rows = supports.get(arm)
        if not isinstance(arm_rows, list):
            errors.append(f"missing_support_arm:{arm}")
            continue
        expected_rows: list[Mapping[str, Any]] = []
        for class_name in CLASSES:
            candidates = ranked.get(class_name, [])
            required = class_counts[class_name]
            if len(candidates) < required:
                errors.append(f"support_pool_short:{arm}:{class_name}")
                continue
            expected_rows.extend(candidates[:required])

        actual_ids = [
            row.get("case_id") if isinstance(row, Mapping) else None
            for row in arm_rows
        ]
        expected_ids = [row["case_id"] for row in expected_rows]
        if actual_ids != expected_ids:
            errors.append(f"selected_id_order:{arm}")
        actual_counts = Counter(
            row.get("class")
            for row in arm_rows
            if isinstance(row, Mapping)
        )
        if len(arm_rows) != sum(class_counts.values()) or any(
            actual_counts.get(name, 0) != class_counts[name]
            for name in CLASSES
        ):
            errors.append(f"support_counts:{arm}")
        if len(arm_rows) == len(expected_rows) and arm_rows != expected_rows:
            errors.append(f"selected_row_content:{arm}")

    return errors
