#!/usr/bin/env python3
"""Raw-only independent audit for scheduler cost allocation #5021."""
import copy
import hashlib
import json
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
POLICIES = ("STABLE_LIST_SCAN", "STABLE_SORTED_LIST", "ELIGIBLE_HEAP")
SIZES = (8, 32, 128, 512, 2048)
BLOCKS = 15


def sha(data):
    return hashlib.sha256(data).hexdigest()


def expected_trace(candidates):
    """Independent declarative oracle; does not import runner.py."""
    return [row[3] for row in sorted(candidates)]


def audit_doc(raw, freeze, schedule, schedule_bytes):
    errors = []
    expected_source = freeze.get("source_sha256")
    if raw.get("schema") != "scheduler-cost-raw-v1":
        errors.append("raw_schema")
    if raw.get("issue") != 5021 or raw.get("parent_issue") != 2868:
        errors.append("issue_identity")
    if raw.get("allocation") != freeze.get("allocation"):
        errors.append("allocation_identity")
    if raw.get("freeze_parent_commit") != freeze.get("freeze_parent_commit"):
        errors.append("freeze_parent_commit")
    if raw.get("source_sha256") != expected_source:
        errors.append("source_hash_manifest")
    if raw.get("schedule_sha256") != sha(schedule_bytes):
        errors.append("schedule_hash")
    if schedule.get("schema") != "scheduler-cost-schedule-v1":
        errors.append("schedule_schema")

    rows = raw.get("rows")
    expected_count = len(SIZES) * BLOCKS * len(POLICIES)
    if (not isinstance(rows, list) or len(rows) != expected_count or
            raw.get("worker_processes_expected") != expected_count or
            raw.get("worker_processes_observed") != expected_count):
        errors.append("worker_denominator")
    if not isinstance(rows, list):
        return errors or ["rows_type"]
    if raw.get("policies") != list(POLICIES) or raw.get("sizes") != list(SIZES):
        errors.append("design_inventory")
    if raw.get("blocks_per_size") != BLOCKS:
        errors.append("block_inventory")

    index = {}
    for envelope in rows:
        if not isinstance(envelope, dict):
            errors.append("row_type")
            continue
        key = (envelope.get("size"), envelope.get("block"), envelope.get("policy"))
        if key in index:
            errors.append("duplicate_worker:" + repr(key))
        index[key] = envelope
        if key[0] not in SIZES or type(key[1]) is not int or not 0 <= key[1] < BLOCKS or key[2] not in POLICIES:
            errors.append("worker_identity:" + repr(key))
        if envelope.get("worker_exit_code") != 0:
            errors.append("worker_exit:" + repr(key))
        if not isinstance(envelope.get("worker_stderr"), str):
            errors.append("worker_stderr_missing:" + repr(key))
        stdout = envelope.get("worker_stdout")
        result = envelope.get("result")
        if not isinstance(stdout, str) or not isinstance(result, dict):
            errors.append("worker_output_missing:" + repr(key))
            continue
        try:
            parsed = json.loads(stdout)
        except Exception:
            errors.append("worker_stdout_invalid:" + repr(key))
            continue
        if parsed != result:
            errors.append("worker_stdout_result_mismatch:" + repr(key))
        if result.get("schema") != "scheduler-cost-worker-v1":
            errors.append("worker_schema:" + repr(key))
        if any(result.get(field) != value for field, value in zip(("size", "block", "policy"), key)):
            errors.append("worker_result_identity:" + repr(key))
        if envelope.get("worker_elapsed_ns_including_startup", 0) <= 0:
            errors.append("worker_elapsed_missing:" + repr(key))
        if type(result.get("process_cpu_ns")) is not int or result["process_cpu_ns"] <= 0:
            errors.append("process_cpu_invalid:" + repr(key))
        if type(result.get("wall_ns")) is not int or result["wall_ns"] <= 0:
            errors.append("wall_time_invalid:" + repr(key))

    expected_keys = {(size, block, policy) for size in SIZES for block in range(BLOCKS)
                     for policy in POLICIES}
    if set(index) != expected_keys:
        errors.append("worker_key_set")

    cases = {row["size"]: row for row in schedule.get("cases", [])}
    for size in SIZES:
        case = cases.get(size)
        if not isinstance(case, dict):
            errors.append("schedule_size_missing:" + str(size))
            continue
        blocks = {row.get("block"): row.get("candidates") for row in case.get("blocks", [])}
        for block in range(BLOCKS):
            candidates = blocks.get(block)
            if not isinstance(candidates, list) or len(candidates) != size:
                errors.append("schedule_candidates:" + str(size) + ":" + str(block))
                continue
            trace = expected_trace(candidates)
            for policy in POLICIES:
                envelope = index.get((size, block, policy))
                if not envelope or not isinstance(envelope.get("result"), dict):
                    continue
                result = envelope["result"]
                if result.get("selected_count") != size or result.get("trace") != trace:
                    errors.append("trace_or_count:" + repr((size, block, policy)))
                trace_bytes = json.dumps(result.get("trace"), separators=(",", ":")).encode()
                if result.get("trace_sha256") != sha(trace_bytes):
                    errors.append("trace_hash:" + repr((size, block, policy)))
            traces = [index.get((size, block, policy), {}).get("result", {}).get("trace")
                      for policy in POLICIES]
            if traces[0] is not None and not (traces[0] == traces[1] == traces[2]):
                errors.append("policy_trace_disagreement:" + repr((size, block)))
    return errors


def timing_summary(raw):
    index = {(r.get("size"), r.get("block"), r.get("policy")): r.get("result")
             for r in raw.get("rows", []) if isinstance(r, dict)}
    ratios = {}
    medians = {}
    for size in SIZES:
        samples = {p: [] for p in POLICIES}
        paired = {p: [] for p in POLICIES if p != "ELIGIBLE_HEAP"}
        for block in range(BLOCKS):
            for policy in POLICIES:
                result = index.get((size, block, policy))
                if isinstance(result, dict) and type(result.get("process_cpu_ns")) is int:
                    samples[policy].append(result["process_cpu_ns"])
        for policy in POLICIES:
            if len(samples[policy]) == BLOCKS:
                medians[(size, policy)] = statistics.median(samples[policy])
        for other in ("STABLE_LIST_SCAN", "STABLE_SORTED_LIST"):
            ratios[(size, other)] = statistics.median(
                index[(size, block, "ELIGIBLE_HEAP")]["process_cpu_ns"] /
                index[(size, block, other)]["process_cpu_ns"]
                for block in range(BLOCKS)
                if all(isinstance(index.get((size, block, p)), dict) and
                       index[(size, block, p)]["process_cpu_ns"] > 0
                       for p in ("ELIGIBLE_HEAP", other))
            ) if all(len(samples[p]) == BLOCKS for p in ("ELIGIBLE_HEAP", other)) else None
    return {
        "median_process_cpu_ns": {
            "%d/%s" % key: value for key, value in sorted(medians.items())
        },
        "median_paired_heap_over_baseline_cpu_ratio": {
            "%d/%s" % key: value for key, value in sorted(ratios.items())
        },
    }


def corruption_controls(raw, freeze, schedule, schedule_bytes):
    mutants = {}
    m = copy.deepcopy(raw); m["rows"].pop(); mutants["drop_worker"] = m
    m = copy.deepcopy(raw); m["rows"].append(copy.deepcopy(m["rows"][0])); mutants["duplicate_worker"] = m
    m = copy.deepcopy(raw); m["source_sha256"]["runner.py"] = "0" * 64; mutants["source_hash"] = m
    m = copy.deepcopy(raw); m["worker_processes_observed"] -= 1; mutants["denominator"] = m
    m = copy.deepcopy(raw); m["rows"][0]["worker_exit_code"] = 1; mutants["worker_exit"] = m
    m = copy.deepcopy(raw); m["rows"][0]["result"]["trace"][0] = "forged"; mutants["trace_edit"] = m
    m = copy.deepcopy(raw); m["rows"][0]["result"]["trace_sha256"] = "f" * 64; mutants["trace_hash"] = m
    m = copy.deepcopy(raw); m["rows"][0]["worker_stdout"] = "{}\n"; mutants["stdout_edit"] = m
    m = copy.deepcopy(raw); m["rows"][0]["worker_stderr"] = None; mutants["stderr_removed"] = m
    m = copy.deepcopy(raw); m["rows"][0]["result"]["process_cpu_ns"] = -1; mutants["negative_cpu"] = m
    m = copy.deepcopy(raw); m["rows"][0]["size"] = 999; mutants["wrong_size"] = m
    m = copy.deepcopy(raw); m["schedule_sha256"] = "0" * 64; mutants["schedule_digest"] = m
    return {name: bool(audit_doc(doc, freeze, schedule, schedule_bytes))
            for name, doc in mutants.items()}


def load_inputs():
    freeze = json.loads((ROOT / "FREEZE.json").read_text(encoding="utf-8"))
    schedule_bytes = (ROOT / "scenarios.json").read_bytes()
    if sha(schedule_bytes) != freeze["schedule_sha256"]:
        raise RuntimeError("SCHEDULE_SHA256_MISMATCH")
    schedule = json.loads(schedule_bytes)
    for name, expected in freeze["source_sha256"].items():
        if sha((ROOT / name).read_bytes()) != expected:
            raise RuntimeError("SOURCE_SHA256_MISMATCH:" + name)
    return freeze, schedule, schedule_bytes


def main():
    if len(sys.argv) != 3:
        raise SystemExit("usage: audit.py RAW_JSON OUTPUT_DIRECTORY")
    freeze, schedule, schedule_bytes = load_inputs()
    raw_bytes = Path(sys.argv[1]).read_bytes()
    raw = json.loads(raw_bytes)
    errors = audit_doc(raw, freeze, schedule, schedule_bytes)
    controls = corruption_controls(raw, freeze, schedule, schedule_bytes)
    summary = timing_summary(raw)
    ratios = summary["median_paired_heap_over_baseline_cpu_ratio"]
    threshold_ok = all(ratios.get("%d/%s" % (size, policy)) is not None and
                       ratios["%d/%s" % (size, policy)] <= 0.80
                       for size in (512, 2048)
                       for policy in ("STABLE_LIST_SCAN", "STABLE_SORTED_LIST"))
    if errors or not all(controls.values()):
        decision = "HOLD_INDEPENDENT_AUDIT"
    elif not threshold_ok:
        decision = "FAIL_HEAP_COST_THRESHOLD_NOT_MET"
    else:
        decision = "PASS_HEAP_COST_CROSSOVER_SCOPED"
    report = {
        "schema": "scheduler-cost-audit-v1", "decision": decision,
        "errors": errors, "rows": len(raw.get("rows", [])),
        "worker_processes_expected": raw.get("worker_processes_expected"),
        "worker_processes_observed": raw.get("worker_processes_observed"),
        "corruption_controls": controls,
        "corruption_controls_rejected": sum(controls.values()),
        "timing_summary": summary,
        "threshold": {"heap_ratio_max": 0.80, "queue_sizes": [512, 2048]},
        "raw_sha256": sha(raw_bytes),
    }
    encoded = (json.dumps(report, sort_keys=True, separators=(",", ":")) + "\n").encode()
    out = Path(sys.argv[2]); out.mkdir(parents=True, exist_ok=True)
    (out / "audit.json").write_bytes(encoded)
    (out / "audit.sha256").write_text(sha(encoded) + "  audit.json\n", encoding="ascii")
    print(encoded.decode(), end="")
    raise SystemExit(0 if decision != "HOLD_INDEPENDENT_AUDIT" else 1)


if __name__ == "__main__":
    main()
