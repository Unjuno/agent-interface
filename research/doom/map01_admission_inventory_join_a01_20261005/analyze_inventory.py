"""Compare V39 per-key admissions with full key sets in aggregate receipts."""
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
FREEZE = json.loads((HERE / "FREEZE.json").read_text(encoding="utf-8"))


def reconstruct(events: list[dict]) -> dict:
    scope = None
    admissions = []
    receipts = []
    for index, event in enumerate(events):
        kind = event.get("event")
        if kind == "step_started":
            scope = {"id": event.get("id"), "step": event.get("step"),
                     "operation": event.get("operation"), "start_index": index}
        elif kind == "input_admission":
            admissions.append({"index": index, "key": event.get("key"),
                               "admitted_ns": event.get("admitted_ns"),
                               "input_ack_ns": event.get("input_ack_ns"),
                               "scope": dict(scope) if scope else None})
        elif kind == "keys_held":
            receipts.append({"index": index, "id": event.get("id"),
                             "step": event.get("step"), "keys": event.get("keys"),
                             "input_ack_ns": event.get("input_ack_ns")})
        elif kind == "step_completed" and scope and event.get("id") == scope["id"] and event.get("step") == scope["step"]:
            scope = None
        elif kind == "terminal" and scope and event.get("id") == scope["id"]:
            scope = None
        elif kind == "cancel_requested" and scope and event.get("id") == scope["id"] and event.get("matched") is True:
            scope = None

    scoped = [row for row in admissions if row["scope"] and row["scope"]["operation"] == "hold"]
    groups = {}
    for row in scoped:
        key = (row["scope"]["id"], row["scope"]["step"])
        groups.setdefault(key, []).append(row)
    comparisons = []
    used_admissions = set()
    for receipt in receipts:
        key = (receipt["id"], receipt["step"])
        group = [row for row in groups.get(key, []) if row["index"] < receipt["index"]]
        admitted_keys = [row["key"] for row in group]
        receipt_keys = receipt["keys"] if type(receipt["keys"]) is list else None
        valid_keys = (receipt_keys is not None and all(type(x) is str and x for x in receipt_keys)
                      and len(set(receipt_keys)) == len(receipt_keys)
                      and all(type(x) is str and x for x in admitted_keys)
                      and len(set(admitted_keys)) == len(admitted_keys))
        status = "EXACT" if valid_keys and set(receipt_keys) == set(admitted_keys) else "MISMATCH"
        comparisons.append({"receipt_index": receipt["index"], "id": receipt["id"],
                            "step": receipt["step"], "receipt_keys": receipt_keys,
                            "admitted_keys": admitted_keys, "status": status})
        if status == "EXACT":
            used_admissions.update(row["index"] for row in group)
    unmatched = [row for row in scoped if row["index"] not in used_admissions]
    counts = {"admissions": len(admissions), "scoped_hold_admissions": len(scoped),
              "aggregate_receipts": len(receipts),
              "exact_key_set_matches": sum(row["status"] == "EXACT" for row in comparisons),
              "key_set_mismatches": sum(row["status"] != "EXACT" for row in comparisons),
              "unmatched_admissions": len(unmatched)}
    return {"schema": "map01-admission-inventory-join-a01-v1", "counts": counts,
            "comparisons": comparisons,
            "unmatched_admissions": [{"index": row["index"], "key": row["key"],
                                      "id": row["scope"]["id"], "step": row["scope"]["step"]}
                                     for row in unmatched]}


def main() -> None:
    spec = FREEZE
    proc = subprocess.run(["git", "show", f"{spec['source_commit']}:{spec['source_path']}"],
                         cwd=HERE, capture_output=True, check=True)
    raw = proc.stdout
    if hashlib.sha256(raw).hexdigest() != spec["source_sha256"]:
        raise RuntimeError("HOLD_SOURCE_HASH_MISMATCH")
    events = [json.loads(line) for line in raw.splitlines()]
    if (len(events), sum(x.get("event") == "input_admission" for x in events),
            sum(x.get("event") == "keys_held" for x in events)) != (634, 39, 28):
        raise RuntimeError("HOLD_SOURCE_CARDINALITY_MISMATCH")
    result = reconstruct(events)
    orphan = result["unmatched_admissions"]
    expected_orphan = [{"index": orphan[0]["index"], "key": "Down",
                        "id": "cover-4", "step": 10}] if len(orphan) == 1 else []
    passed = (result["counts"] == {"admissions": 39, "scoped_hold_admissions": 39,
                                   "aggregate_receipts": 28, "exact_key_set_matches": 28,
                                   "key_set_mismatches": 0, "unmatched_admissions": 1}
              and orphan == expected_orphan)
    report = {**result,
              "allocation": spec["allocation"],
              "status": "PASS_ADMISSION_INVENTORY_JOIN_SCOPED" if passed else "COUNTEREXAMPLE",
              "source_sha256": hashlib.sha256(raw).hexdigest(),
              "scope": "retained V39 event-stream admission/aggregate-ack key-set comparison; no per-key key-up"}
    (HERE / "candidate-output.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    raise SystemExit(0 if passed else 1)


if __name__ == "__main__":
    main()
