"""Construction-only coverage audit for the #5139 synthetic prompt pool."""
from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
from typing import Any

from make_dataset import build
from protocol import TEMPLATES


FORMAL_TEST_SEED = 73194111
SUPPORT_TEST_SEED = 51829177
HELDOUT_SELECTION_TEST_SEED = 97101021
ALLOCATION = "qwen5139-construction-only-fixture"
FIELDS = ("display_name", "timezone", "digest_frequency", "sharing_visibility")


def set_features(row: Mapping[str, Any], split: str) -> tuple[int, str]:
    intent = row["intent"]
    field = intent.get("field")
    state = row["state"]
    old = state["values"][field]
    value = intent["value"]
    template_ids = [
        i for i, template in enumerate(TEMPLATES[split])
        if template.format(field=field, old=old, value=value) == row["task"]
    ]
    if row.get("class") != "set" or len(template_ids) != 1 or field not in FIELDS:
        raise ValueError("set_template_or_field_not_reconstructible")
    return template_ids[0], field


def counts(rows: Sequence[Mapping[str, Any]], split: str) -> dict[str, Any]:
    templates: Counter[str] = Counter()
    fields: Counter[str] = Counter()
    for row in rows:
        template, field = set_features(row, split)
        templates[str(template)] += 1
        fields[field] += 1
    return {"n": len(rows), "template": dict(sorted(templates.items())),
            "field": dict(sorted(fields.items()))}


def _rank(seed: int, split: str, template: int, field: str, case_id: str) -> bytes:
    material = (
        b"support-row-coverage-rank-v1\n" + str(seed).encode("ascii") + b"\n"
        + split.encode("ascii") + b"\n" + str(template).encode("ascii") + b"\n"
        + field.encode("utf-8") + b"\n" + case_id.encode("utf-8")
    )
    return hashlib.sha256(material).digest()


def stratified_set_order(
    rows: Sequence[Mapping[str, Any]], seed: int, split: str
) -> list[Mapping[str, Any]]:
    """Deterministically round-robin 4x4 template/field cells; never seed-search."""
    buckets: dict[tuple[int, str], list[Mapping[str, Any]]] = defaultdict(list)
    for row in rows:
        if row.get("class") == "set":
            template, field = set_features(row, split)
            buckets[(template, field)].append(row)
    for template in range(4):
        for field in FIELDS:
            if not buckets[(template, field)]:
                raise ValueError(f"coverage_cell_missing:{split}:{template}:{field}")
            buckets[(template, field)].sort(
                key=lambda row: (
                    _rank(seed, split, template, field, row["case_id"]),
                    row["case_id"].encode("utf-8"),
                )
            )
    order: list[Mapping[str, Any]] = []
    max_depth = max(len(bucket) for bucket in buckets.values())
    for depth in range(max_depth):
        for template in range(4):
            field = FIELDS[(template + depth) % 4]
            bucket = buckets[(template, field)]
            if depth < len(bucket):
                order.append(bucket[depth])
    return order


def analyze() -> dict[str, Any]:
    data = build(FORMAL_TEST_SEED, SUPPORT_TEST_SEED, ALLOCATION)
    pool = data["support_pool"]
    heldout_pool = data["heldout_pool"]
    old_imbalanced = [r for r in pool if r["class"] == "set"][:16]
    old_balanced = [r for r in pool if r["class"] == "set"][:4]
    hash_imbalanced = [r for r in data["supports"]["imbalanced"] if r["class"] == "set"]
    hash_balanced = [r for r in data["supports"]["balanced"] if r["class"] == "set"]
    heldout_prefix = [r for r in heldout_pool if r["class"] == "set"][:8]
    matched_support = stratified_set_order(pool, SUPPORT_TEST_SEED, "support")
    matched_heldout = stratified_set_order(
        heldout_pool, HELDOUT_SELECTION_TEST_SEED, "heldout"
    )
    return {
        "schema": "qwen5139-set-template-field-coverage-construction-v1",
        "formal_test_seed": FORMAL_TEST_SEED,
        "support_test_seed": SUPPORT_TEST_SEED,
        "heldout_selection_test_seed": HELDOUT_SELECTION_TEST_SEED,
        "seed_search": False,
        "current_hash_rank": {
            "balanced_set": counts(hash_balanced, "support"),
            "imbalanced_set": counts(hash_imbalanced, "support"),
            "heldout_prefix": counts(heldout_prefix, "heldout"),
        },
        "old_prefix_reference": {
            "balanced_set": counts(old_balanced, "support"),
            "imbalanced_set": counts(old_imbalanced, "support"),
        },
        "stratified_candidate": {
            "balanced_set": counts(matched_support[:4], "support"),
            "imbalanced_set": counts(matched_support[:16], "support"),
            "heldout_set": counts(matched_heldout[:8], "heldout"),
            "support_nested": (
                {r["case_id"] for r in matched_support[:4]}
                <= {r["case_id"] for r in matched_support[:16]}
            ),
            "heldout_rows_shared": True,
        },
        "scope": "synthetic set-class template/field marginals only; no model or outcome",
    }


if __name__ == "__main__":
    print(json.dumps(analyze(), sort_keys=True, indent=2))
