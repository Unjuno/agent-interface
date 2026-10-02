#!/usr/bin/env python3
"""Independent raw-only CPU audit for allocation a09."""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

SEED = 49720261009
WORKERS = 6
NUMEL = 24 * 1024 * 1024
OPS = 20
WORKING_BYTES = NUMEL * 8
EXPECTED_DEVICE = "NVIDIA GeForce RTX 3080 Laptop GPU"
MIN_INITIAL_FREE = 10 * 1024**3
MIN_GLOBAL_FREE = 4 * 1024**3
MAX_AGGREGATE_ALLOCATED = 8 * 1024**3
MIN_DEVICE_BYTES = 16 * 1024**3


def _integer(row: dict, key: str) -> int | None:
    value = row.get(key)
    return value if type(value) is int else None


def audit_rows(rows: list[dict]) -> list[str]:
    errors: list[str] = []
    if len(rows) != WORKERS:
        errors.append(f"expected {WORKERS} rows, got {len(rows)}")
    if any(not isinstance(row, dict) for row in rows):
        return errors + ["each candidate row must be a JSON object"]
    ids = [_integer(row, "worker_id") for row in rows]
    if any(worker_id is None for worker_id in ids) or set(ids) != set(range(WORKERS)):
        errors.append("worker IDs must be exactly 0..5 with no duplicates")
    pids = [_integer(row, "pid") for row in rows]
    if any(pid is None or pid <= 0 for pid in pids) or len(set(pids)) != len(pids):
        errors.append("worker PIDs must be positive and unique")

    aggregate_peak = 0
    for row in rows:
        worker_id = _integer(row, "worker_id")
        prefix = f"worker {worker_id}"
        if row.get("seed") != SEED:
            errors.append(f"{prefix}: seed mismatch")
        if row.get("status") != "ok":
            errors.append(f"{prefix}: status is not ok")
        if row.get("device") != EXPECTED_DEVICE:
            errors.append(f"{prefix}: device mismatch")
        if _integer(row, "numel") != NUMEL or _integer(row, "ops") != OPS:
            errors.append(f"{prefix}: work contract mismatch")
        allocated = _integer(row, "allocated_bytes")
        if allocated != WORKING_BYTES:
            errors.append(f"{prefix}: allocated working set is not exactly 192 MiB")
        peak = _integer(row, "peak_allocated_bytes")
        total = _integer(row, "device_total_bytes")
        if peak is None or total is None:
            errors.append(f"{prefix}: allocator/device memory fields are malformed")
        else:
            aggregate_peak += peak
            if total < MIN_DEVICE_BYTES or peak > int(total * 0.05):
                errors.append(f"{prefix}: device size or 5% allocator cap mismatch")
        overlap_free = _integer(row, "global_free_overlap_bytes")
        if overlap_free is None or overlap_free < MIN_GLOBAL_FREE:
            errors.append(f"{prefix}: synchronized global free VRAM below 4 GiB")
        initial_value = (SEED % 997) + (worker_id if worker_id is not None else 0) * 11
        expected = NUMEL * (initial_value + OPS)
        if _integer(row, "initial_value") != initial_value:
            errors.append(f"{prefix}: initial value mismatch")
        if _integer(row, "expected_checksum") != expected or _integer(row, "checksum") != expected:
            errors.append(f"{prefix}: independently reconstructed checksum mismatch")
    if aggregate_peak > MAX_AGGREGATE_ALLOCATED:
        errors.append("aggregate worker allocator peak exceeds 8 GiB")
    return errors


def audit_host_rows(samples: list[dict[str, str]]) -> list[str]:
    errors: list[str] = []
    if not samples:
        return ["host GPU telemetry is empty"]
    free_values: list[int] = []
    for index, sample in enumerate(samples, 1):
        try:
            free_bytes = int(float(sample["memory_free_mib"]) * 1024**2)
            float(sample["utilization_gpu_pct"])
            float(sample["memory_used_mib"])
            free_values.append(free_bytes)
        except Exception:
            errors.append(f"host GPU telemetry row {index} malformed")
    if free_values:
        if free_values[0] < MIN_INITIAL_FREE:
            errors.append("host GPU telemetry baseline free VRAM below 10 GiB")
        if min(free_values) < MIN_GLOBAL_FREE:
            errors.append("host GPU telemetry free VRAM fell below 4 GiB")
    return errors


def main(argv: list[str]) -> int:
    if len(argv) != 4:
        print("usage: audit.py candidate.jsonl host_gpu_samples.csv audit.json", file=sys.stderr)
        return 2
    source, samples_path, destination = map(Path, argv[1:])
    rows = []
    parse_errors = []
    for line_number, line in enumerate(source.read_text(encoding="utf-8").splitlines(), 1):
        try:
            rows.append(json.loads(line))
        except Exception as exc:
            parse_errors.append(f"line {line_number}: {type(exc).__name__}: {exc}")
    try:
        with samples_path.open(newline="", encoding="utf-8") as stream:
            samples = list(csv.DictReader(stream))
        sample_errors = audit_host_rows(samples)
    except Exception as exc:
        sample_errors = [f"host GPU telemetry parse failed: {type(exc).__name__}: {exc}"]
    errors = parse_errors + audit_rows(rows) + sample_errors
    result = {
        "schema": "gpu-a09-audit-v1",
        "status": "PASS" if not errors else "FAIL",
        "candidate_rows": len(rows),
        "host_samples": len(samples) if "samples" in locals() else 0,
        "errors": errors,
    }
    destination.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
