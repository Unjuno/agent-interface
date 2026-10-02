"""Fresh construction-only dataset generator for the #5139 sampler contract.

This is an additive successor fixture. Allocation and formal seeds must be
provided only by a separately frozen study plan; tests use synthetic sentinels.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from protocol import SCHEMA, expected_bound, make_rows, simulate_bound
from sampler import CLASSES, COUNTS, select_support


def row_class(row: dict[str, Any]) -> str:
    intent = row["intent"]
    if intent["op"] in ("yield", "no_action"):
        return intent["op"] + ":" + intent["reason"]
    return intent["op"]


def annotate(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    for row in rows:
        row["class"] = row_class(row)
        row["expected_bound"] = expected_bound(row)
        row["expected_effect"] = simulate_bound(row["expected_bound"], row["state"])
    return rows


def build(seed: int, support_seed: int, allocation: str) -> dict[str, Any]:
    if isinstance(seed, bool) or not isinstance(seed, int) or seed <= 0:
        raise ValueError("formal_seed_must_be_positive_integer")
    if isinstance(support_seed, bool) or not isinstance(support_seed, int) or support_seed <= 0:
        raise ValueError("support_seed_must_be_positive_integer")
    if not isinstance(allocation, str) or not allocation:
        raise ValueError("allocation_must_be_nonempty")

    support_pool = annotate(make_rows(support_seed, "support", 128))
    heldout_pool = annotate(make_rows(seed, "heldout", 256))
    grouped_heldout: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in heldout_pool:
        grouped_heldout[row["class"]].append(row)
    heldout: list[dict[str, Any]] = []
    for name in CLASSES:
        if len(grouped_heldout[name]) < 8:
            raise ValueError(f"heldout_short:{name}")
        heldout.extend(grouped_heldout[name][:8])

    imbalanced_by_class, balanced_by_class = select_support(support_pool, support_seed)
    supports = {
        "imbalanced": [row for name in CLASSES for row in imbalanced_by_class[name]],
        "balanced": [row for name in CLASSES for row in balanced_by_class[name]],
    }
    support_counts = {
        arm: dict(counts) for arm, counts in COUNTS.items()
    }
    all_ids = [r["case_id"] for r in support_pool + heldout_pool]
    if len(all_ids) != len(set(all_ids)):
        raise ValueError("case_id_collision")
    support_scopes = {r["state"]["scope_id"] for r in support_pool}
    heldout_scopes = {r["state"]["scope_id"] for r in heldout_pool}
    if support_scopes & heldout_scopes:
        raise ValueError("scope_leakage")
    support_tasks = {r["task"] for r in support_pool}
    heldout_tasks = {r["task"] for r in heldout_pool}
    if support_tasks & heldout_tasks:
        raise ValueError("task_leakage")

    return {
        "schema": SCHEMA + "-balanced-support-v1",
        "allocation": allocation,
        "seed": seed,
        "support_seed": support_seed,
        "classes": list(CLASSES),
        "support_pool": support_pool,
        "support_counts": support_counts,
        "supports": supports,
        "heldout_pool": heldout_pool,
        "heldout": heldout,
        "heldout_selection": {
            name: [r["case_id"] for r in grouped_heldout[name][:8]]
            for name in CLASSES
        },
        "split_contract": (
            "support and heldout use disjoint prompt template families, "
            "case ids, scopes, and generated values"
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--support-seed", type=int, required=True)
    parser.add_argument("--allocation", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    document = build(args.seed, args.support_seed, args.allocation)
    payload = (json.dumps(document, sort_keys=True, separators=(",", ":")) + "\n").encode()
    Path(args.out).write_bytes(payload)
    print(json.dumps({
        "bytes": len(payload),
        "sha256": hashlib.sha256(payload).hexdigest(),
        "support_pool": len(document["support_pool"]),
        "heldout_pool": len(document["heldout_pool"]),
        "heldout": len(document["heldout"]),
        "support_counts": document["support_counts"],
    }, sort_keys=True))


if __name__ == "__main__":
    main()
