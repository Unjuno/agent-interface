#!/usr/bin/env python3
"""Emit the frozen blocked/mixed practice-order schedule ledger."""

import hashlib
import json
import sys
import copy
from pathlib import Path


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def build_raw(source, source_bytes):
    arms = {"blocked": list(source["blocked_order"]), "mixed": list(source["mixed_order"])}
    rows = {}
    for arm, task_order in arms.items():
        rows[arm] = []
        for index, task_id in enumerate(task_order):
            task = source["tasks"][task_id]
            rows[arm].append({
                "slot": index,
                "task_id": task_id,
                "variant_id": task["variant_id"],
                "demonstrated_fact_ids": list(task["demonstrated_fact_ids"]),
                "support_offer_id": task["support_offer_id"],
                "hint_profile": task["hint_profile"],
                "stop_available": task["stop_available"],
                "skip_available": task["skip_available"],
            })
    return {
        "format": "practice-order-6600-raw-v1",
        "allocation": source["allocation"],
        "source_sha256": hashlib.sha256(source_bytes).hexdigest(),
        "arms": arms,
        "rows": rows,
        "assessment_history": copy.deepcopy(source["assessment_history"]),
        "execution": {"candidate_actions": 0, "task_effects": 0, "participants": 0},
    }


def main(argv):
    if len(argv) != 3:
        raise SystemExit("usage: candidate.py SOURCE.json RAW.json")
    source_path, output_path = map(Path, argv[1:])
    source_bytes = source_path.read_bytes()
    source = json.loads(source_bytes)
    raw = build_raw(source, source_bytes)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(json.dumps(raw, indent=2, sort_keys=True).encode() + b"\n")
    print(json.dumps({"status": "CANDIDATE_COMPLETE", "arms": len(raw["arms"]), "rows": sum(map(len, raw["rows"].values()))}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
