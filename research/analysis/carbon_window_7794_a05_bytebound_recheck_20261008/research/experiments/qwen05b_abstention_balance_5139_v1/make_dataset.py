"""Generate a fresh paired #5139 dataset from the exact current-main protocol."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from protocol import SCHEMA, expected_bound, make_rows, simulate_bound
from sampler import CLASSES, COUNTS, select_support


def _positive_seed(value: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError("seed_must_be_positive_integer")
    return value


def _rank(seed: int, class_name: str, case_id: str) -> bytes:
    material = (b"heldout-row-rank-v1\n" + str(seed).encode("ascii") + b"\n"
                + class_name.encode("utf-8") + b"\n" + case_id.encode("utf-8"))
    return hashlib.sha256(material).digest()


def row_class(row):
    intent = row["intent"]
    return intent["op"] + ":" + intent["reason"] if intent["op"] in ("yield", "no_action") else intent["op"]


def annotate(rows):
    result = []
    for source in rows:
        row = dict(source)
        row["class"] = row_class(row)
        row["expected_bound"] = expected_bound(row)
        row["expected_effect"] = simulate_bound(row["expected_bound"], row["state"])
        result.append(row)
    return result


def build(formal_seed: int, support_seed: int, heldout_seed: int):
    formal_seed, support_seed, heldout_seed = map(_positive_seed, (formal_seed, support_seed, heldout_seed))
    if len({formal_seed, support_seed, heldout_seed}) != 3:
        raise ValueError("seeds_must_be_distinct")
    support_pool = annotate(make_rows(support_seed, "support", 128))
    heldout_pool = annotate(make_rows(heldout_seed, "heldout", 256))
    if {r["class"] for r in support_pool} != set(CLASSES) or {r["class"] for r in heldout_pool} != set(CLASSES):
        raise ValueError("class_coverage_incomplete")
    imbalanced_by_class, balanced_by_class = select_support(support_pool, support_seed)
    supports = {
        "imbalanced": [r for name in CLASSES for r in imbalanced_by_class[name]],
        "balanced": [r for name in CLASSES for r in balanced_by_class[name]],
    }
    heldout_groups = {name: [r for r in heldout_pool if r["class"] == name] for name in CLASSES}
    heldout_by_class = {}
    for name, group in heldout_groups.items():
        ranked = sorted(group, key=lambda r: (_rank(heldout_seed, name, r["case_id"]), r["case_id"].encode("utf-8")))
        if len(ranked) < 8:
            raise ValueError(f"heldout_pool_short:{name}:{len(ranked)}")
        heldout_by_class[name] = ranked[:8]
    heldout = [r for name in CLASSES for r in heldout_by_class[name]]
    all_ids = [r["case_id"] for r in support_pool + heldout_pool]
    all_scopes = [r["state"]["scope_id"] for r in support_pool + heldout_pool]
    if len(all_ids) != len(set(all_ids)) or len(all_scopes) != len(set(all_scopes)):
        raise ValueError("id_or_scope_collision")
    if {r["state"]["scope_id"] for r in support_pool} & {r["state"]["scope_id"] for r in heldout_pool}:
        raise ValueError("scope_leakage")
    if {r["task"] for r in support_pool} & {r["task"] for r in heldout_pool}:
        raise ValueError("task_leakage")
    selected = {arm: {name: [r["case_id"] for r in rows if r["class"] == name] for name in CLASSES}
                for arm, rows in supports.items()}
    return {
        "schema": SCHEMA + "-balanced-support-v2",
    "allocation": "qwen5139-support-balance-currentmain-eddcf7a4-20260930-02",
        "formal_seed": formal_seed,
        "support_seed": support_seed,
        "heldout_seed": heldout_seed,
        "classes": list(CLASSES),
        "support_pool": support_pool,
        "support_counts": COUNTS,
        "supports": supports,
        "support_selected_case_ids": selected,
        "heldout_pool": heldout_pool,
        "heldout": heldout,
        "heldout_selection": {name: [r["case_id"] for r in heldout_by_class[name]] for name in CLASSES},
        "split_contract": "support and heldout use disjoint pools, seeds, case ids, scopes, and task strings",
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--formal-seed", type=int, required=True)
    ap.add_argument("--support-seed", type=int, required=True)
    ap.add_argument("--heldout-seed", type=int, required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    doc = build(args.formal_seed, args.support_seed, args.heldout_seed)
    payload = (json.dumps(doc, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
    Path(args.out).write_bytes(payload)
    summary = {"bytes":len(payload), "sha256":hashlib.sha256(payload).hexdigest(),
               "support_pool":len(doc["support_pool"]), "heldout_pool":len(doc["heldout_pool"]),
               "heldout":len(doc["heldout"]), "support_rows":{k:len(v) for k,v in doc["supports"].items()}}
    print(json.dumps(summary, sort_keys=True))


if __name__ == "__main__":
    main()
