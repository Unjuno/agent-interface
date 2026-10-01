#!/usr/bin/env python3
"""Independent raw-only auditor. Does not import or execute runner.py."""
import argparse
import hashlib
import json
import math
from pathlib import Path

import torch
import torch.nn.functional as F

torch.set_num_threads(1)
try:
    torch.set_num_interop_threads(1)
except RuntimeError:
    # The construction suite imports trainer and auditor in one process;
    # formal execution uses separate containers/processes for both.
    pass
torch.use_deterministic_algorithms(True)


def canonical_sha(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def ten(x):
    return torch.tensor(x, dtype=torch.float32)


def oracle(base, adapter, x):
    # A query record is one [8] feature vector. Add the batch axis so F.linear
    # returns [1,4]; selecting row zero must retain all four logits.
    z = F.linear(ten(x).unsqueeze(0), ten(base["w1"]), ten(base["b1"]))
    h = torch.tanh(z)
    effective = ten(base["w2"]) + ten(adapter["b"]) @ ten(adapter["a"])
    return F.linear(h, effective, ten(base["b2"]))[0]


def valid_logits(logits):
    return logits.ndim == 1 and logits.numel() == 4


def percentile(values, q):
    ordered = sorted(values)
    return ordered[max(0, math.ceil(q * len(ordered)) - 1)] if ordered else None


def stable_generation(before, after):
    return before == after and before % 2 == 0


def available_version(before, after, published):
    return before == after and str(before) in published


def audit_one(path):
    raw = json.loads(path.read_text(encoding="utf-8"))
    errors = []
    if raw.get("schema") != "needle-concurrent-online-lora.raw.v2":
        errors.append("schema")
    if raw.get("authority") is not False or raw.get("action_emissions") != 0:
        errors.append("authority_or_effect")
    base_sha = canonical_sha(raw["base"])
    if base_sha != raw.get("base_sha256") or base_sha != raw.get("immutable_base_after_sha256"):
        errors.append("base_digest_or_immutability")
    task = raw["task"]
    teacher, tb = ten(task["teacher"]), ten(task["teacher_b"])
    qx = ten(task["query_x"])
    expected_y = (qx @ teacher.T + tb).argmax(dim=1).tolist()
    if expected_y != task["query_y"]:
        errors.append("query_labels")
    sx = ten(task["support_x"])
    if (sx @ teacher.T + tb).argmax(dim=2).tolist() != task["support_y"]:
        errors.append("support_labels")
    arm = raw["arm"]
    published = raw["published"]
    for version, item in published.items():
        state = dict(item)
        claimed = state.pop("sha256", None)
        if claimed != canonical_sha(state):
            errors.append(f"snapshot_digest:{version}")
    if len(raw["queries"]) != raw["constants"]["queries"]:
        errors.append("query_count")
    if arm != "BASELINE" and (len(raw["training_steps"]) != 12 * 16 or raw["worker_errors"]):
        errors.append("training_count_or_worker_error")
    correct, latencies, misses, overlap = 0, [], 0, 0
    stable_live, unstable_live = 0, 0
    intervals = raw["training_intervals"]
    for rec in raw["queries"]:
        i = rec["index"]
        if i >= len(expected_y) or rec["label"] != expected_y[i] or rec["x"] != task["query_x"][i]:
            errors.append(f"query_binding:{i}")
            continue
        logits = torch.tensor(rec["logits"], dtype=torch.float32)
        if not valid_logits(logits):
            errors.append(f"logit_shape:{i}")
            continue
        correct += int(int(torch.argmax(logits)) == expected_y[i])
        latencies.append(rec["latency_ns"] / 1e6)
        misses += int(rec["deadline_miss"])
        actual_overlap = any(a < rec["end_ns"] and b > rec["start_ns"] for a, b in intervals)
        overlap += int(actual_overlap)
        if bool(rec["train_interval_overlap"]) != actual_overlap:
            errors.append(f"overlap_flag:{i}")
        if arm == "SHARED_LIVE":
            g0, g1 = rec["generation_before"], rec["generation_after"]
            flagged = (g0 != g1 or g0 % 2 == 1)
            if rec["writer_overlap"] != flagged:
                errors.append(f"generation_flag:{i}")
            if stable_generation(g0, g1):
                stable_live += 1
                item = published.get(str(g0 // 2))
                if item is None or not torch.equal(oracle(raw["base"], item, rec["x"]), logits):
                    errors.append(f"stable_live_recompute:{i}")
            else:
                unstable_live += 1
        else:
            v0, v1 = rec["version_before"], rec["version_after"]
            if v0 != v1:
                errors.append(f"version_changed_during_inference:{i}")
            item = published.get(str(v0))
            if item is None or not torch.equal(oracle(raw["base"], item, rec["x"]), logits):
                errors.append(f"proposal_recompute:{i}")
    return {"seed": raw["seed"], "arm": arm, "queries": len(raw["queries"]),
        "updates": len(raw["training_steps"]), "accuracy": correct / max(1, len(raw["queries"])),
        "inference_p50_ms": percentile(latencies, 0.50), "inference_p95_ms": percentile(latencies, 0.95),
        "deadline_misses": misses, "training_overlap_queries": overlap,
        "shared_live_stable_queries": stable_live, "shared_live_unstable_queries": unstable_live,
        "final_version": max((int(x) for x in published), default=0), "errors": errors}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--raw", required=True)
    p.add_argument("--out", required=True)
    args = p.parse_args()
    rows = [audit_one(x) for x in sorted(Path(args.raw).glob("seed_*.json"))]
    errors = [f"{x['seed']}:{x['arm']}:{e}" for x in rows for e in x["errors"]]
    cow = [x for x in rows if x["arm"] == "COW"]
    if len(rows) != 9 or len(cow) != 3:
        errors.append("formal_cell_count")
    gates = {"all_cow_overlap_at_least_8": len(cow) == 3 and all(x["training_overlap_queries"] >= 8 for x in cow),
             "all_cow_p95_le_16_67ms": len(cow) == 3 and all(x["inference_p95_ms"] <= 16.67 for x in cow),
             "all_cow_zero_deadlines_missed": len(cow) == 3 and all(x["deadline_misses"] == 0 for x in cow),
             "audit_zero_errors": len(errors) == 0}
    if errors:
        decision = "FAIL_VERSION_INTEGRITY"
    elif not gates["all_cow_overlap_at_least_8"]:
        decision = "HOLD_NO_CONCURRENCY_PRESSURE"
    elif not gates["all_cow_p95_le_16_67ms"] or not gates["all_cow_zero_deadlines_missed"]:
        decision = "HOLD_LATENCY_BUDGET"
    else:
        decision = "PASS_COW_CONCURRENT_SYSTEM1_SCOPED"
    result = {"schema": "needle-concurrent-online-lora.audit.v1", "decision": decision,
              "errors": errors, "gates": gates, "cells": rows}
    Path(args.out).write_text(json.dumps(result, sort_keys=True, indent=2)+"\n", encoding="utf-8")
    print(json.dumps({"decision": decision, "errors": len(errors), "gates": gates}, sort_keys=True), flush=True)
    raise SystemExit(0 if not errors else 2)


if __name__ == "__main__":
    main()
