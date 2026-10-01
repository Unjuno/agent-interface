#!/usr/bin/env python3
"""Independent raw-only CPU audit for allocation a08."""
from __future__ import annotations

import json
import sys
from pathlib import Path

SEED = 49720261008
WORKERS = 6
NUMEL = 24 * 1024 * 1024
OPS = 20
WORKING_BYTES = NUMEL * 8
EXPECTED_DEVICE = "NVIDIA GeForce RTX 3080 Laptop GPU"
MIN_GLOBAL_FREE = 4 * 1024**3
MAX_AGGREGATE_ALLOCATED = 8 * 1024**3


def audit_rows(rows: list[dict]) -> list[str]:
    errors: list[str] = []
    ids = [row.get("worker_id") for row in rows]
    if len(rows) != WORKERS:
        errors.append(f"expected {WORKERS} rows, got {len(rows)}")
    if sorted(ids) != list(range(WORKERS)):
        errors.append("worker IDs must be exactly 0..5 with no duplicates")
    aggregate_peak = 0
    for row in rows:
        worker_id = row.get("worker_id")
        prefix = f"worker {worker_id}"
        if row.get("seed") != SEED:
            errors.append(f"{prefix}: seed mismatch")
        if row.get("status") != "ok":
            errors.append(f"{prefix}: status is not ok")
        if row.get("device") != EXPECTED_DEVICE:
            errors.append(f"{prefix}: device mismatch")
        if row.get("numel") != NUMEL or row.get("ops") != OPS:
            errors.append(f"{prefix}: work contract mismatch")
        if row.get("allocated_bytes", 0) < WORKING_BYTES:
            errors.append(f"{prefix}: allocated working set below 192 MiB")
        if row.get("peak_allocated_bytes", 0) > int(row.get("device_total_bytes", 0) * 0.05):
            errors.append(f"{prefix}: allocator peak exceeded 5% device cap")
        aggregate_peak += row.get("peak_allocated_bytes", 0)
        if row.get("global_free_overlap_bytes", 0) < MIN_GLOBAL_FREE:
            errors.append(f"{prefix}: synchronized global free VRAM below 4 GiB")
        initial = (SEED % 997) + (worker_id if isinstance(worker_id, int) else 0) * 11
        expected = NUMEL * (initial + OPS)
        if row.get("initial_value") != initial:
            errors.append(f"{prefix}: initial value mismatch")
        if row.get("expected_checksum") != expected or row.get("checksum") != expected:
            errors.append(f"{prefix}: independently reconstructed checksum mismatch")
    if aggregate_peak > MAX_AGGREGATE_ALLOCATED:
        errors.append("aggregate worker allocator peak exceeds 8 GiB")
    return errors


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        print("usage: audit.py candidate.jsonl audit.json", file=sys.stderr)
        return 2
    source, destination = map(Path, argv[1:])
    rows = []
    parse_errors = []
    for line_number, line in enumerate(source.read_text(encoding="utf-8").splitlines(), 1):
        try:
            rows.append(json.loads(line))
        except Exception as exc:
            parse_errors.append(f"line {line_number}: {type(exc).__name__}: {exc}")
    errors = parse_errors + audit_rows(rows)
    result = {"schema": "gpu-a08-audit-v1", "status": "PASS" if not errors else "FAIL",
              "rows": len(rows), "errors": errors}
    destination.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
