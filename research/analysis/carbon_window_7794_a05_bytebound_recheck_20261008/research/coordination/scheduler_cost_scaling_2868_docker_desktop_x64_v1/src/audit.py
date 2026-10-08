"""Independent raw-only auditor; does not import runner, worker, or generator."""
import copy
import hashlib
import json
import statistics
import sys
from pathlib import Path

SIZES = (8, 32, 128, 512, 2048)
BLOCKS = 15
POLICIES = ("STABLE_LIST_SCAN", "STABLE_SORTED_LIST", "ELIGIBLE_HEAP")
EXPECTED_SCHEDULE_SHA256 = "f778860219a8a9ffe8014eb00eeb41456dac1bf58a2687ee64045a2b9e1df733"


def digest(data):
    return hashlib.sha256(data).hexdigest()


def oracle(candidates):
    return [c["op_id"] for c in sorted(
        candidates,
        key=lambda c: (-c["priority"], c["deadline"], c["enqueue_seq"], c["op_id"]),
    )]


def audit(raw, schedule, exercise_controls=True):
    errors = []
    if raw.get("schema") != "scheduler-cost-scaling-raw-v1":
        errors.append("schema")
    schedule_bytes = (json.dumps(schedule, sort_keys=True, separators=(",", ":")) + "\n").encode()
    if digest(schedule_bytes) != EXPECTED_SCHEDULE_SHA256 or raw.get("schedule_sha256") != EXPECTED_SCHEDULE_SHA256:
        errors.append("schedule_sha256")
    if schedule.get("schema") != "scheduler-cost-scaling-docker-desktop-x64-v1":
        errors.append("schedule_schema")
    if schedule.get("sizes") != list(SIZES) or schedule.get("policies") != list(POLICIES):
        errors.append("schedule_dimensions")
    for size in SIZES:
        try:
            data = schedule["sizes_data"][str(size)]
            candidates = data["candidates"]
            blocks = data["blocks"]
            if len(candidates) != size or len(blocks) != BLOCKS:
                errors.append("schedule_count")
            if any(type(c.get("ready")) is not bool or c["ready"] is not True or c.get("expires") is not None
                   for c in candidates):
                errors.append("eligibility")
            if any(type(c.get("priority")) is not int or type(c.get("deadline")) is not int
                   or type(c.get("enqueue_seq")) is not int or not isinstance(c.get("op_id"), str)
                   for c in candidates):
                errors.append("candidate_types")
            if len({c["op_id"] for c in candidates}) != size or {c["enqueue_seq"] for c in candidates} != set(range(size)):
                errors.append("candidate_identity")
            if len({(c["priority"], c["deadline"]) for c in candidates}) >= size:
                errors.append("schedule_ties_absent")
            if [b.get("block") for b in blocks] != list(range(BLOCKS)) or any(
                b.get("policy_order") is None or len(b["policy_order"]) != len(POLICIES)
                or set(b["policy_order"]) != set(POLICIES) for b in blocks
            ):
                errors.append("block_schedule")
        except (KeyError, TypeError):
            errors.append("schedule_shape")
    expected_count = len(SIZES) * BLOCKS * len(POLICIES)
    rows = raw.get("rows")
    if not isinstance(rows, list) or raw.get("worker_count") != expected_count or len(rows) != expected_count:
        errors.append("denominator")
        rows = rows if isinstance(rows, list) else []
    seen = set()
    observed_order = []
    expected_order = [
        (size, block["block"], policy)
        for size in SIZES
        for block in schedule["sizes_data"][str(size)]["blocks"]
        for policy in block["policy_order"]
    ]
    timings = {size: {policy: [] for policy in POLICIES} for size in SIZES}
    traces = {}
    for row in rows:
        if not isinstance(row, dict):
            errors.append("row_type")
            continue
        try:
            size, block, policy = row["size"], row["block"], row["policy"]
            if type(size) is not int or type(block) is not int or not isinstance(policy, str):
                errors.append("identity_types")
                continue
            key = (size, block, policy)
            if key in seen or size not in SIZES or block not in range(BLOCKS) or policy not in POLICIES:
                errors.append("identity")
                continue
            seen.add(key)
            observed_order.append(key)
            if type(row.get("exit")) is not int or row["exit"] != 0 or row.get("stderr") != "":
                errors.append("worker_exit")
            if type(row.get("wrapper_elapsed_ns")) is not int or row["wrapper_elapsed_ns"] <= 0:
                errors.append("wrapper_time")
            stdout = row.get("stdout")
            if not isinstance(stdout, str) or row.get("stdout_sha256") != digest(stdout.encode()):
                errors.append("stdout_binding")
                continue
            result = json.loads(stdout)
            if result.get("policy") != policy:
                errors.append("policy_binding")
            if type(result.get("cpu_ns")) is not int or result["cpu_ns"] <= 0:
                errors.append("cpu_time")
            if type(result.get("wall_ns")) is not int or result["wall_ns"] <= 0:
                errors.append("wall_time")
            if type(row.get("worker_cpu_ns")) is not int or row["worker_cpu_ns"] != result.get("cpu_ns"):
                errors.append("cpu_binding")
            if type(row.get("worker_wall_ns")) is not int or row["worker_wall_ns"] != result.get("wall_ns"):
                errors.append("wall_binding")
            trace_hash = digest(json.dumps(result.get("trace"), separators=(",", ":")).encode())
            if row.get("trace_sha256") != trace_hash:
                errors.append("trace_binding")
            candidates = schedule["sizes_data"][str(size)]["candidates"]
            expected_trace = oracle(candidates)
            if result.get("trace") != expected_trace:
                errors.append("trace_oracle")
            timings[size][policy].append(result["cpu_ns"])
            traces[(size, block, policy)] = result.get("trace")
        except (KeyError, TypeError, ValueError, json.JSONDecodeError):
            errors.append("parse_or_shape")
    if len(seen) != expected_count:
        errors.append("coverage")
    if observed_order != expected_order:
        errors.append("worker_order")
    for size in SIZES:
        for block in schedule["sizes_data"][str(size)]["blocks"]:
            block_id = block["block"]
            block_traces = [traces.get((size, block_id, policy)) for policy in POLICIES]
            if any(trace is None for trace in block_traces) or not all(t == block_traces[0] for t in block_traces):
                errors.append("paired_trace")
    ratios = {}
    for size in SIZES:
        if any(len(timings[size][policy]) != BLOCKS for policy in POLICIES):
            errors.append("timing_coverage")
            continue
        scan = statistics.median(timings[size]["STABLE_LIST_SCAN"])
        sorted_list = statistics.median(timings[size]["STABLE_SORTED_LIST"])
        heap = statistics.median(timings[size]["ELIGIBLE_HEAP"])
        ratios[str(size)] = {
            "median_paired_heap_over_scan": statistics.median(
                h / s for h, s in zip(timings[size]["ELIGIBLE_HEAP"], timings[size]["STABLE_LIST_SCAN"])
            ),
            "median_paired_heap_over_sorted_list": statistics.median(
                h / s for h, s in zip(timings[size]["ELIGIBLE_HEAP"], timings[size]["STABLE_SORTED_LIST"])
            ),
            "median_cpu_ns": {"scan": scan, "sorted_list": sorted_list, "heap": heap},
        }
    if exercise_controls and not errors:
        controls = {}
        bad = copy.deepcopy(raw)
        bad["rows"].pop()
        controls["missing_worker_rejected"] = bool(audit(bad, schedule, False)["errors"])
        bad = copy.deepcopy(raw)
        altered = json.loads(bad["rows"][0]["stdout"])
        altered["trace"][0] = "altered-op"
        bad["rows"][0]["stdout"] = json.dumps(altered, sort_keys=True, separators=(",", ":"))
        bad["rows"][0]["stdout_sha256"] = digest(bad["rows"][0]["stdout"].encode())
        controls["trace_mutation_rejected"] = bool(audit(bad, schedule, False)["errors"])
        bad = copy.deepcopy(raw)
        bad["rows"][0]["exit"] = True
        controls["bool_exit_rejected"] = bool(audit(bad, schedule, False)["errors"])
        bad = copy.deepcopy(raw)
        bad["schedule_sha256"] = "0" * 64
        controls["schedule_digest_rejected"] = bool(audit(bad, schedule, False)["errors"])
        bad = copy.deepcopy(raw)
        payload = json.loads(bad["rows"][0]["stdout"])
        payload["cpu_ns"] += 1
        bad["rows"][0]["stdout"] = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        bad["rows"][0]["stdout_sha256"] = digest(bad["rows"][0]["stdout"].encode())
        controls["recomputed_timing_mutation_rejected"] = bool(audit(bad, schedule, False)["errors"])
    else:
        controls = {}
    controls_pass = len(controls) == 5 and all(value is True for value in controls.values())
    if exercise_controls and not controls_pass:
        errors.append("corruption_controls")
    return {
        "status": "HOLD_AUDIT" if errors else "PASS_AUDIT_AND_TRACES",
        "errors": errors,
        "row_count": len(rows),
        "expected_row_count": expected_count,
        "unique_rows": len(seen),
        "ratios": ratios,
        "corruption_controls": controls,
        "corruption_controls_rejected": sum(controls.values()),
        "corruption_control_count": len(controls),
    }


if __name__ == "__main__":
    raw = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    schedule = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
    result = audit(raw, schedule)
    Path(sys.argv[3]).write_text(json.dumps(result, sort_keys=True, indent=2) + "\n",
                                 encoding="utf-8", newline="\n")
    print(json.dumps(result, sort_keys=True))
    raise SystemExit(0 if result["status"] == "PASS_AUDIT_AND_TRACES" else 1)
