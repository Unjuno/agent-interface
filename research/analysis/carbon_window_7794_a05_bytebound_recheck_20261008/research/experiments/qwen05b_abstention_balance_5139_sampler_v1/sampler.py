"""Deterministic class-conditional support ranking for Issue #5139."""

from __future__ import annotations

import hashlib
from collections import defaultdict
from collections.abc import Iterable, Mapping
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


def row_rank(seed: int, class_name: str, case_id: str) -> bytes:
    """Return a stable rank, independent of input row order and Python RNG version."""
    if isinstance(seed, bool) or not isinstance(seed, int) or seed <= 0:
        raise ValueError("seed_must_be_positive_integer")
    if not class_name or not case_id:
        raise ValueError("rank_fields_must_be_nonempty")
    material = (
        b"support-row-rank-v1\n"
        + str(seed).encode("ascii")
        + b"\n"
        + class_name.encode("utf-8")
        + b"\n"
        + case_id.encode("utf-8")
    )
    return hashlib.sha256(material).digest()


def rank_support_rows(
    rows: Iterable[Mapping[str, Any]], seed: int
) -> dict[str, list[Mapping[str, Any]]]:
    """Validate and rank a shared support pool independently within each class."""
    grouped: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    seen_ids: set[str] = set()
    for row in rows:
        class_name = row.get("class")
        case_id = row.get("case_id")
        if class_name not in CLASSES:
            raise ValueError(f"unknown_class:{class_name!r}")
        if not isinstance(case_id, str) or not case_id:
            raise ValueError("case_id_must_be_nonempty_string")
        if case_id in seen_ids:
            raise ValueError(f"duplicate_case_id:{case_id}")
        seen_ids.add(case_id)
        grouped[class_name].append(row)

    missing = [name for name in CLASSES if name not in grouped]
    if missing:
        raise ValueError("missing_classes:" + ",".join(missing))

    ranked: dict[str, list[Mapping[str, Any]]] = {}
    for class_name in CLASSES:
        ranked[class_name] = sorted(
            grouped[class_name],
            key=lambda row: (
                row_rank(seed, class_name, row["case_id"]),
                row["case_id"].encode("utf-8"),
            ),
        )
    return ranked


def select_support(
    rows: Iterable[Mapping[str, Any]], seed: int
) -> tuple[dict[str, list[Mapping[str, Any]]], dict[str, list[Mapping[str, Any]]]]:
    """Select both arms as prefixes of the same per-class ranked lists."""
    ranked = rank_support_rows(rows, seed)
    selected: dict[str, dict[str, list[Mapping[str, Any]]]] = {
        arm: {} for arm in COUNTS
    }
    for class_name in CLASSES:
        required = max(counts[class_name] for counts in COUNTS.values())
        candidates = ranked[class_name]
        if len(candidates) < required:
            raise ValueError(f"pool_short:{class_name}:{len(candidates)}<{required}")
        for arm, counts in COUNTS.items():
            selected[arm][class_name] = candidates[: counts[class_name]]
    return selected["imbalanced"], selected["balanced"]
