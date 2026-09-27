#!/usr/bin/env python3
"""Independent raw-only auditor for Issue #5044."""
import argparse
import copy
import hashlib
import json
import statistics
import sys
from pathlib import Path

SIZES = (8, 32, 128, 512, 2048)
BLOCKS = 15
POLICIES = ("STABLE_LIST_SCAN", "STABLE_SORTED_LIST", "ELIGIBLE_HEAP")


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read_inputs(root):
    freeze = json.loads((root / "FREEZE.json").read_text(encoding="utf-8"))
    for name, expected in freeze["source_sha256"].items():
        if sha((root / name).read_bytes()) != expected:
            raise ValueError("SOURCE_SHA256_MISMATCH:" + name)
    schedule_bytes = (root.parent / "input" / "scenarios.json").read_bytes()
    if sha(schedule_bytes) != freeze["schedule_sha256"]:
        raise ValueError("SCHEDULE_SHA256_MISMATCH")
    return freeze, json.loads(schedule_bytes)


def oracle(candidates):
    return [row[3] for row in sorted((tuple(item) for item in candidates))]


def expected_map(schedule):
    result = {}
    for case in schedule["cases"]:
        for block in case["blocks"]:
            result[(case["size"], block["block"])] = oracle(block["candidates"])
    return result


def inspect(raw, freeze, schedule):
    errors = []
    if raw.get("schema") != "scheduler-cost-import-boundary-raw-v1":
        errors.append("RAW_SCHEMA")
    if raw.get("issue") != 5044 or raw.get("allocation") != freeze["allocation"]:
        errors.append("RAW_IDENTITY")
    if raw.get("source_sha256") != freeze["source_sha256"]:
        errors.append("RAW_SOURCE_BINDING")
    if raw.get("schedule_sha256") != freeze["schedule_sha256"]:
        errors.append("RAW_SCHEDULE_BINDING")
    if raw.get("worker_processes_expected") != 225 or raw.get("worker_processes_observed") != 225:
        errors.append("DENOMINATOR")
    if tuple(raw.get("sizes", [])) != SIZES or raw.get("blocks_per_size") != BLOCKS:
        errors.append("SCHEDULE_DIMENSIONS")
    if tuple(raw.get("policies", [])) != POLICIES:
        errors.append("POLICY_SET")
    expected = expected_map(schedule)
    seen = set()
    by_case = {}
    rows = raw.get("rows")
    if not isinstance(rows, list) or len(rows) != 225:
        errors.append("ROW_COUNT")
        rows = rows if isinstance(rows, list) else []
    for row in rows:
        if not isinstance(row, dict):
            errors.append("ROW_TYPE")
            continue
        key = (row.get("size"), row.get("block"), row.get("policy"))
        if key in seen or key[2] not in POLICIES or (key[0], key[1]) not in expected:
            errors.append("ROW_IDENTITY_OR_DUPLICATE")
            continue
        seen.add(key)
        if row.get("worker_exit_code") != 0 or row.get("worker_parse_error") is not None:
            errors.append("WORKER_EXIT_OR_PARSE")
        result = row.get("result")
        if not isinstance(result, dict):
            errors.append("MISSING_RESULT")
            continue
        try:
            stdout_result = json.loads(row.get("worker_stdout", ""))
        except (TypeError, json.JSONDecodeError):
            stdout_result = None
        if stdout_result != result:
            errors.append("WORKER_STDOUT_BINDING")
        if (result.get("schema") != "scheduler-cost-import-boundary-worker-v1" or
                result.get("size") != key[0] or result.get("block") != key[1] or
                result.get("policy") != key[2]):
            errors.append("WORKER_BINDING")
        if result.get("schedule_sha256") != freeze["schedule_sha256"]:
            errors.append("WORKER_SCHEDULE_BINDING")
        if result.get("heapq_loaded_before_timer") is not True:
            errors.append("HEAPQ_TIMING_BOUNDARY")
        cpu = result.get("queue_process_cpu_ns")
        wall = result.get("queue_wall_ns")
        if type(cpu) is not int or cpu <= 0 or type(wall) is not int or wall <= 0:
            errors.append("TIMING_VALUE")
        if result.get("trace") != expected.get((key[0], key[1])):
            errors.append("TRACE_ORACLE")
        trace_digest = sha(json.dumps(result.get("trace"), separators=(",", ":")).encode())
        if result.get("trace_sha256") != trace_digest:
            errors.append("TRACE_DIGEST")
        if result.get("selected_count") != key[0]:
            errors.append("SELECTED_COUNT")
        if isinstance(cpu, int) and cpu > 0:
            by_case.setdefault((key[0], key[1]), {})[key[2]] = cpu
    required = {(size, block, policy) for size in SIZES for block in range(BLOCKS)
                for policy in POLICIES}
    if seen != required:
        errors.append("ROW_COVERAGE")
    ratios = {}
    for size in (512, 2048):
        for baseline in ("STABLE_LIST_SCAN", "STABLE_SORTED_LIST"):
            paired = []
            for block in range(BLOCKS):
                group = by_case.get((size, block), {})
                if "ELIGIBLE_HEAP" not in group or baseline not in group:
                    errors.append("RATIO_COVERAGE")
                    break
                paired.append(group["ELIGIBLE_HEAP"] / group[baseline])
            if len(paired) == BLOCKS:
                ratios[f"{size}:heap/{baseline}"] = statistics.median(paired)
    threshold_pass = all(ratios.get(f"{size}:heap/{base}", float("inf")) <= 0.80
                         for size in (512, 2048)
                         for base in ("STABLE_LIST_SCAN", "STABLE_SORTED_LIST"))
    if errors:
        decision = "HOLD_EVIDENCE_INCOMPLETE"
    elif threshold_pass:
        decision = "PASS_HEAP_COST_CROSSOVER_SCOPED"
    else:
        decision = "FAIL_HEAP_COST_THRESHOLD_NOT_MET"
    return {"errors": errors, "decision": decision, "ratios": ratios,
            "rows_reconciled": len(seen), "trace_oracle_rows": sum(
                1 for row in rows if isinstance(row, dict) and isinstance(row.get("result"), dict)
                and row["result"].get("trace") == expected.get((row.get("size"), row.get("block"))))}


def mutate(raw, which):
    changed = copy.deepcopy(raw)
    if which == "remove_row":
        changed["rows"].pop()
    elif which == "duplicate_row":
        changed["rows"].append(copy.deepcopy(changed["rows"][0]))
        changed["worker_processes_observed"] = 226
    elif which == "issue":
        changed["issue"] = 5021
    elif which == "allocation":
        changed["allocation"] = "other-allocation"
    elif which == "source_hash":
        changed["source_sha256"]["runner.py"] = "0" * 64
    elif which == "schedule_hash":
        changed["schedule_sha256"] = "0" * 64
    elif which == "worker_exit":
        changed["rows"][0]["worker_exit_code"] = 1
    elif which == "missing_result":
        changed["rows"][0]["result"] = None
    elif which == "trace":
        changed["rows"][0]["result"]["trace"][0] = "corrupt-op"
    elif which == "policy":
        changed["rows"][0]["policy"] = "UNKNOWN"
    elif which == "timing_boundary":
        changed["rows"][0]["result"]["heapq_loaded_before_timer"] = False
    elif which == "cpu":
        changed["rows"][0]["result"]["queue_process_cpu_ns"] = -1
    elif which == "stdout":
        changed["rows"][0]["worker_stdout"] = "{}\n"
    return changed


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True,
                        help="read-only mounted package root containing src/ and input/")
    parser.add_argument("--raw", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    freeze, schedule = read_inputs(root / "src")
    raw_bytes = args.raw.read_bytes()
    raw = json.loads(raw_bytes)
    result = inspect(raw, freeze, schedule)
    controls = []
    for name in ("remove_row", "duplicate_row", "issue", "allocation", "source_hash",
                 "schedule_hash", "worker_exit", "missing_result", "trace", "policy",
                 "timing_boundary", "cpu", "stdout"):
        audit = inspect(mutate(raw, name), freeze, schedule)
        controls.append({"name": name, "rejected": bool(audit["errors"])})
    result["controls"] = controls
    result["controls_rejected"] = sum(item["rejected"] for item in controls)
    result["controls_expected"] = len(controls)
    if result["controls_rejected"] != len(controls):
        result["errors"].append("CORRUPTION_CONTROL_GAP")
        result["decision"] = "HOLD_EVIDENCE_INCOMPLETE"
    report = {"schema": "scheduler-cost-import-boundary-audit-v1",
              "raw_sha256": sha(raw_bytes), "source_sha256": freeze["source_sha256"],
              "schedule_sha256": freeze["schedule_sha256"], **result}
    encoded = (json.dumps(report, sort_keys=True, separators=(",", ":")) + "\n").encode()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_bytes(encoded)
    print(encoded.decode(), end="")
    return 0 if not report["errors"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
