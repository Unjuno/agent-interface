#!/usr/bin/env python3
"""Independent raw-only CPU auditor for WSLc allocation a10."""
from __future__ import annotations

import copy
import csv
import json
import sys
from pathlib import Path

ALLOCATION = "GPU-MEMORY-SHARING-4972-20261002-10"
SEED = 49720261010
WORKERS = 6
NUMEL = 24 * 1024 * 1024
OPS = 20
WORKING_BYTES = NUMEL * 8
EXPECTED_DEVICE = "NVIDIA GeForce RTX 3080 Laptop GPU"
MIN_INITIAL_FREE = 10 * 1024**3
MIN_GLOBAL_FREE = 4 * 1024**3
MAX_AGGREGATE_PEAK = 8 * 1024**3
MIN_DEVICE_BYTES = 16 * 1024**3


def _integer(row: dict, key: str) -> int | None:
    value = row.get(key)
    return value if type(value) is int else None


def audit_rows(rows: list[dict]) -> list[str]:
    errors: list[str] = []
    if len(rows) != WORKERS:
        errors.append(f"expected {WORKERS} worker rows, got {len(rows)}")
    if any(not isinstance(row, dict) for row in rows):
        return errors + ["each worker record must be a JSON object"]
    ids = [_integer(row, "worker_id") for row in rows]
    if any(value is None for value in ids) or set(ids) != set(range(WORKERS)):
        errors.append("worker IDs must be exactly 0..5 with no duplicates")
    pids = [_integer(row, "pid") for row in rows]
    if any(value is None or value <= 0 for value in pids) or len(set(pids)) != len(pids):
        errors.append("worker PIDs must be positive and unique")

    aggregate_peak = 0
    for row in rows:
        worker_id = _integer(row, "worker_id")
        label = f"worker {worker_id}"
        if row.get("seed") != SEED or row.get("status") != "ok":
            errors.append(f"{label}: seed or status mismatch")
        if row.get("device") != EXPECTED_DEVICE:
            errors.append(f"{label}: device mismatch")
        if _integer(row, "numel") != NUMEL or _integer(row, "ops") != OPS:
            errors.append(f"{label}: work contract mismatch")
        if _integer(row, "allocated_bytes") != WORKING_BYTES:
            errors.append(f"{label}: allocation is not exactly 192 MiB")
        total = _integer(row, "device_total_bytes")
        peak = _integer(row, "peak_allocated_bytes")
        if total is None or peak is None or total < MIN_DEVICE_BYTES:
            errors.append(f"{label}: device or allocator memory fields malformed")
        else:
            aggregate_peak += peak
            if peak > int(total * 0.05):
                errors.append(f"{label}: allocator peak exceeds the 5% per-process cap")
        for field in ("global_free_before_bytes", "global_free_overlap_bytes", "global_free_after_bytes"):
            value = _integer(row, field)
            if value is None or value < MIN_GLOBAL_FREE:
                errors.append(f"{label}: {field} below 4 GiB or malformed")
        initial = (SEED % 997) + (worker_id if worker_id is not None else 0) * 11
        checksum = NUMEL * (initial + OPS)
        if _integer(row, "initial_value") != initial:
            errors.append(f"{label}: initial value mismatch")
        if _integer(row, "checksum") != checksum or _integer(row, "expected_checksum") != checksum:
            errors.append(f"{label}: independent checksum reconstruction mismatch")
    if aggregate_peak > MAX_AGGREGATE_PEAK:
        errors.append("aggregate worker allocator peak exceeds 8 GiB")
    return errors


def audit_host_rows(samples: list[dict[str, str]]) -> list[str]:
    errors: list[str] = []
    if len(samples) < 2:
        return ["host GPU telemetry requires at least two samples"]
    free_values: list[int] = []
    for index, sample in enumerate(samples, 1):
        try:
            if not sample.get("timestamp"):
                raise ValueError("missing timestamp")
            free_values.append(int(float(sample["memory_free_mib"]) * 1024**2))
            float(sample["utilization_gpu_pct"])
            float(sample["memory_used_mib"])
        except Exception:
            errors.append(f"host telemetry row {index} malformed")
    if free_values:
        if free_values[0] < MIN_INITIAL_FREE:
            errors.append("baseline free VRAM below 10 GiB")
        if min(free_values) < MIN_GLOBAL_FREE:
            errors.append("host-sampled free VRAM fell below 4 GiB")
    return errors


def mutation_controls(rows: list[dict], samples: list[dict[str, str]]) -> list[dict]:
    cases = []
    duplicate = copy.deepcopy(rows)
    if duplicate:
        duplicate[-1]["worker_id"] = duplicate[0].get("worker_id")
    cases.append(("duplicate_worker_id", audit_rows(duplicate), []))

    checksum = copy.deepcopy(rows)
    if checksum and isinstance(checksum[0].get("checksum"), int):
        checksum[0]["checksum"] += 1
    cases.append(("forged_checksum", audit_rows(checksum), []))

    threshold = copy.deepcopy(samples)
    if threshold:
        threshold[-1]["memory_free_mib"] = str(MIN_GLOBAL_FREE / 1024**2 - 1)
    cases.append(("below_global_free_reserve", [], audit_host_rows(threshold)))

    allocator = copy.deepcopy(rows)
    if allocator and isinstance(allocator[0].get("peak_allocated_bytes"), int):
        allocator[0]["peak_allocated_bytes"] = int(allocator[0].get("device_total_bytes", 0) * 0.05) + 1
    cases.append(("allocator_cap_overrun", audit_rows(allocator), []))
    return [{"mutation": name, "rejected": bool(row_errors or telemetry_errors)} for name, row_errors, telemetry_errors in cases]


def main(argv: list[str]) -> int:
    if len(argv) != 5:
        print("usage: audit.py candidate.jsonl candidate_summary.json host_gpu_samples.csv audit.json", file=sys.stderr)
        return 2
    candidate_path, summary_path, samples_path, audit_path = map(Path, argv[1:])
    errors: list[str] = []
    try:
        rows = [json.loads(line) for line in candidate_path.read_text(encoding="utf-8").splitlines()]
    except Exception as exc:
        rows = []
        errors.append(f"candidate JSONL parse failed: {type(exc).__name__}: {exc}")
    try:
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
    except Exception as exc:
        summary = {}
        errors.append(f"candidate summary parse failed: {type(exc).__name__}: {exc}")
    try:
        with samples_path.open(newline="", encoding="utf-8") as stream:
            samples = list(csv.DictReader(stream))
    except Exception as exc:
        samples = []
        errors.append(f"host telemetry parse failed: {type(exc).__name__}: {exc}")

    errors.extend(audit_rows(rows))
    errors.extend(audit_host_rows(samples))
    if summary.get("allocation") != ALLOCATION or summary.get("seed") != SEED:
        errors.append("candidate summary allocation or seed mismatch")
    if summary.get("candidate_exit_ok") is not True or summary.get("workers_recorded") != WORKERS:
        errors.append("candidate summary does not record successful complete execution")
    if summary.get("worker_exitcodes") != [0] * WORKERS:
        errors.append("one or more worker processes did not exit cleanly")
    observed_count = summary.get("host_samples_observed_during_candidate")
    observed_min = summary.get("host_free_min_bytes_observed_during_candidate")
    if type(observed_count) is not int or observed_count < 2 or observed_count > len(samples):
        errors.append("candidate-time host telemetry count is malformed or inconsistent")
    if type(observed_min) is not int or observed_min < MIN_GLOBAL_FREE:
        errors.append("candidate-time host telemetry minimum below 4 GiB or malformed")

    mutations = mutation_controls(rows, samples)
    if not all(item["rejected"] for item in mutations):
        errors.append("one or more semantic mutation controls were accepted")
    result = {
        "schema": "gpu-a10-audit-v1",
        "allocation": ALLOCATION,
        "status": "PASS_SCOPED" if not errors else "FAIL_AUDIT",
        "worker_rows": len(rows),
        "host_samples": len(samples),
        "mutations": mutations,
        "errors": errors,
    }
    audit_path.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
