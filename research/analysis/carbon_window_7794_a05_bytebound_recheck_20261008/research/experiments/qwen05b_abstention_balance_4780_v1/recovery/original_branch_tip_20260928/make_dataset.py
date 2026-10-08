from __future__ import annotations

import argparse
import hashlib
import json
from collections import defaultdict
from pathlib import Path

from protocol import SCHEMA, expected_bound, make_rows, simulate_bound

CLASSES = (
    "set", "save", "toggle", "yield:forbidden", "yield:ambiguous",
    "yield:stale_scope", "yield:missing_evidence", "no_action:already_satisfied",
)


def row_class(row):
    intent = row["intent"]
    if intent["op"] in ("yield", "no_action"):
        return intent["op"] + ":" + intent["reason"]
    return intent["op"]


def annotate(rows):
    for row in rows:
        row["class"] = row_class(row)
        row["expected_bound"] = expected_bound(row)
        row["expected_effect"] = simulate_bound(row["expected_bound"], row["state"])
    return rows


def select_support(pool):
    grouped = defaultdict(list)
    for row in pool:
        grouped[row["class"]].append(row)
    counts = {
        "imbalanced": {
            "set": 16, "save": 4, "toggle": 4, "yield:forbidden": 1,
            "yield:ambiguous": 1, "yield:stale_scope": 1,
            "yield:missing_evidence": 1, "no_action:already_satisfied": 4,
        },
        "balanced": {name: 4 for name in CLASSES},
    }
    chosen = {}
    for arm, requirements in counts.items():
        rows = []
        for name in CLASSES:
            candidates = grouped[name]
            if len(candidates) < requirements[name]:
                raise ValueError(f"pool_short:{name}:{len(candidates)}")
            rows.extend(candidates[:requirements[name]])
        chosen[arm] = rows
    return chosen, {arm: counts[arm] for arm in counts}


def build(seed):
    support_seed = seed ^ 0xA5A5A5A5
    support_pool = annotate(make_rows(support_seed, "support", 128))
    heldout_pool = annotate(make_rows(seed, "heldout", 256))
    groups = defaultdict(list)
    for row in heldout_pool:
        groups[row["class"]].append(row)
    heldout = []
    for name in CLASSES:
        if len(groups[name]) < 8:
            raise ValueError(f"heldout_short:{name}")
        heldout.extend(groups[name][:8])
    supports, counts = select_support(support_pool)
    all_ids = [r["case_id"] for r in support_pool + heldout_pool]
    if len(all_ids) != len(set(all_ids)):
        raise ValueError("case_id_collision")
    if {r["state"]["scope_id"] for r in support_pool} & {r["state"]["scope_id"] for r in heldout_pool}:
        raise ValueError("scope_leakage")
    if {r["task"] for r in support_pool} & {r["task"] for r in heldout_pool}:
        raise ValueError("task_leakage")
    for arm, rows in supports.items():
        actual = {name: sum(r["class"] == name for r in rows) for name in CLASSES}
        if actual != counts[arm]:
            raise ValueError(f"support_counts:{arm}")
    return {
        "schema": SCHEMA + "-balanced-support-v1",
        "allocation": "qwen05b-abstention-balance-4780-20260928-01",
        "seed": seed,
        "support_seed": support_seed,
        "classes": list(CLASSES),
        "support_pool": support_pool,
        "support_counts": counts,
        "supports": supports,
        "heldout_pool": heldout_pool,
        "heldout": heldout,
        "heldout_selection": {name: [r["case_id"] for r in groups[name][:8]] for name in CLASSES},
        "split_contract": "support and heldout use disjoint prompt template families, case ids, scopes, and generated values",
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    document = build(args.seed)
    payload = (json.dumps(document, sort_keys=True, separators=(",", ":")) + "\n").encode()
    Path(args.out).write_bytes(payload)
    print(json.dumps({"bytes": len(payload), "sha256": hashlib.sha256(payload).hexdigest(),
                      "support_pool": len(document["support_pool"]),
                      "heldout_pool": len(document["heldout_pool"]),
                      "heldout": len(document["heldout"]),
                      "support_counts": document["support_counts"]}, sort_keys=True))


if __name__ == "__main__":
    main()
