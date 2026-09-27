#!/usr/bin/env python3
"""Audit whether the frozen #3807 artifact retains per-feedback accuracy."""

from __future__ import annotations

import argparse
import ast
import base64
import gzip
import hashlib
import json
from pathlib import Path


PINS = {
    "runner.py": "43e6e6ef39883e78e50c3887b2ddf804a755f0305cad0d9ef6f640b00bdccdff",
    "FORMAL_RESULT.json": "abf9a01dd4dc34bc137bf4c25d191372ddceb8c872b3df73a61cdc9c30defc06",
    "audit.py": "d7f76504328a9492a8fe8f83be773e6b1a5a344e6da7cd0e4bd96192fec8bd7a",
}
EXPECTED_SEEDS = [3451, 3452, 3453, 3454, 3455]
ARMS = ("rank2_online", "rank4_online")
N_TEST = 4096


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_bytes(path: Path, expected_hash: str) -> bytes:
    data = path.read_bytes()
    if sha256(data) != expected_hash:
        raise ValueError(f"FROZEN_HASH_MISMATCH:{path.name}")
    return data


def eval_rows_calls(node: ast.AST) -> list[int]:
    return [
        call.lineno
        for call in ast.walk(node)
        if isinstance(call, ast.Call)
        and isinstance(call.func, ast.Name)
        and call.func.id == "eval_rows"
    ]


def run(runner_path: Path, result_path: Path, auditor_path: Path) -> dict:
    runner = load_bytes(runner_path, PINS["runner.py"])
    result_bytes = load_bytes(result_path, PINS["FORMAL_RESULT.json"])
    auditor = load_bytes(auditor_path, PINS["audit.py"])
    envelope = json.loads(result_bytes)
    raw = gzip.decompress(base64.b64decode(envelope["gzip_b64"], validate=True))
    if sha256(raw) != envelope["sha256"] or len(raw) != envelope["raw_bytes"]:
        raise ValueError("CANONICAL_RAW_BINDING_MISMATCH")

    module = ast.parse(runner)
    one_seed = next(
        node
        for node in module.body
        if isinstance(node, ast.FunctionDef) and node.name == "one_seed"
    )
    feedback_loop = next(
        node
        for node in ast.walk(one_seed)
        if isinstance(node, ast.For)
        and isinstance(node.iter, ast.Name)
        and node.iter.id == "feedback_order"
    )
    calls_inside_feedback = eval_rows_calls(feedback_loop)
    call_sites = eval_rows_calls(one_seed)
    if calls_inside_feedback or len(call_sites) != 1:
        raise ValueError("UNEXPECTED_HELDOUT_EVALUATION_PLACEMENT")

    raw_obj = json.loads(raw)
    rows = raw_obj["seeds"]
    if [row["seed"] for row in rows] != EXPECTED_SEEDS:
        raise ValueError("SEED_SET_MISMATCH")

    per_seed = []
    curves_present = []
    for row in rows:
        metrics = row["metrics"]
        timings = row["feedback_ms"]
        item = {"seed": row["seed"]}
        for arm in ARMS:
            metric = metrics[arm]
            if len(timings[arm]) != 16:
                raise ValueError(f"FEEDBACK_TIMING_COUNT:{row['seed']}:{arm}")
            if len(metric["expected"]) != N_TEST or len(metric["predictions"]) != N_TEST:
                raise ValueError(f"FINAL_ROW_EVIDENCE_COUNT:{row['seed']}:{arm}")
            correct = sum(
                expected == predicted
                for expected, predicted in zip(metric["expected"], metric["predictions"])
            )
            if correct != metric["correct"]:
                raise ValueError(f"FINAL_ACCURACY_RECOMPUTE_MISMATCH:{row['seed']}:{arm}")
            for key in ("learning_curve", "accuracy_by_feedback", "per_feedback_accuracy"):
                if key in metric:
                    curves_present.append(f"{row['seed']}:{arm}:{key}")
            item[f"{arm}_timings"] = len(timings[arm])
            item[f"{arm}_final_rows"] = len(metric["expected"])
            item[f"{arm}_final_accuracy"] = correct / N_TEST
        per_seed.append(item)

    namespace: dict = {}
    exec(compile(auditor, "frozen-audit.py", "exec"), namespace)
    original_audit = namespace["audit"](envelope)
    if original_audit["disposition"] != "FAIL_ONLINE_RANK_CAPACITY_GPU":
        raise ValueError("PREDECESSOR_VERDICT_CHANGED_OR_AUDIT_MISMATCH")

    # The frozen runner has no evaluation call in the feedback loop, so the
    # required after-each-arrival accuracy values cannot exist in its output.
    disposition = "HOLD_LEARNING_CURVE_NOT_RECORDED"
    return {
        "disposition": disposition,
        "runner_sha256": sha256(runner),
        "formal_result_sha256": sha256(result_bytes),
        "auditor_sha256": sha256(auditor),
        "canonical_raw_sha256": sha256(raw),
        "canonical_raw_bytes": len(raw),
        "eval_rows_calls_inside_feedback_loop": calls_inside_feedback,
        "eval_rows_call_sites_one_seed": call_sites,
        "per_seed": per_seed,
        "curves_present": curves_present,
        "preserved_predecessor_disposition": original_audit["disposition"],
        "scope": "read-only source and retained-result completeness; no training/prediction/optimizer/evaluation rerun",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runner", type=Path, required=True)
    parser.add_argument("--formal-result", type=Path, required=True)
    parser.add_argument("--auditor", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(run(args.runner, args.formal_result, args.auditor), sort_keys=True))


if __name__ == "__main__":
    main()
