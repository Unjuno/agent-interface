import hashlib
import json
import math
import statistics
import sys
from pathlib import Path

import numpy as np


EXPECTED_SOURCE_SHA256 = "PENDING_RUNNER_SHA"
EXPECTED = {
    "allocation": "MAP01-ROI-BREAK-EVEN-59-GPU-20261001-02",
    "dimensions_wh": [(95, 50), (320, 200), (640, 400), (1280, 800)],
    "batches": [1, 4, 16],
    "warmups": 3,
    "repeats": 21,
    "seed": 59020261002,
    "delta": 32,
    "minimum": 100,
}


def main() -> int:
    if len(sys.argv) != 2:
        print(json.dumps({"status": "STOP_AUDIT_PATH_REQUIRED"}, sort_keys=True))
        return 2
    raw_bytes = Path(sys.argv[1]).read_bytes()
    raw = json.loads(raw_bytes)
    errors = []
    if raw.get("schema") != "map01-roi-gpu-break-even-raw-v2":
        errors.append("schema")
    if raw.get("allocation") != EXPECTED["allocation"]:
        errors.append("allocation")
    if raw.get("source_sha256") != EXPECTED_SOURCE_SHA256:
        errors.append("source_sha256")
    cfg = raw.get("config", {})
    expected_cfg = {
        "dimensions_wh": [list(x) for x in EXPECTED["dimensions_wh"]],
        "batches": EXPECTED["batches"],
        "warmups": EXPECTED["warmups"],
        "repeats": EXPECTED["repeats"],
        "seed": EXPECTED["seed"],
    }
    if cfg != expected_cfg:
        errors.append("config")
    thresholds = raw.get("thresholds", {})
    if thresholds != {"channel_max_delta_exclusive": 32, "changed_pixels_minimum_inclusive": 100}:
        errors.append("thresholds")
    cells = raw.get("cells")
    expected_keys = [(w, h, b) for w, h in EXPECTED["dimensions_wh"] for b in EXPECTED["batches"]]
    if not isinstance(cells, list) or len(cells) != len(expected_keys) or raw.get("cell_count") != len(expected_keys):
        errors.append("cell_cardinality")
        cells = cells if isinstance(cells, list) else []

    rng = np.random.default_rng(EXPECTED["seed"])
    seen = []
    parity = True
    for index, key in enumerate(expected_keys):
        if index >= len(cells) or not isinstance(cells[index], dict):
            errors.append(f"cell_{index}_missing")
            continue
        cell = cells[index]
        w, h, batch = key
        if (cell.get("width"), cell.get("height"), cell.get("batch")) != key:
            errors.append(f"cell_{index}_identity")
        before = rng.integers(0, 256, size=(batch, h, w, 3), dtype=np.uint8)
        after = rng.integers(0, 256, size=(batch, h, w, 3), dtype=np.uint8)
        fixture_sha = hashlib.sha256(before.tobytes() + after.tobytes()).hexdigest()
        if cell.get("fixture_sha256") != fixture_sha:
            errors.append(f"cell_{index}_fixture")
        counts = np.max(np.abs(before.astype(np.int16) - after.astype(np.int16)), axis=-1) > 32
        oracle = counts.sum(axis=(-2, -1), dtype=np.int64).tolist()
        cpu_rows = cell.get("cpu_rows")
        cuda_rows = cell.get("cuda_rows")
        expected_batch_rows = [oracle] * 21
        if cell.get("cpu_counts") != oracle or cell.get("cuda_counts") != oracle:
            errors.append(f"cell_{index}_count_parity")
            parity = False
        if cpu_rows != expected_batch_rows or cuda_rows != expected_batch_rows:
            errors.append(f"cell_{index}_repeat_count_parity")
            parity = False
        if cell.get("cpu_rows_all_match") is not True or cell.get("cuda_rows_all_match") is not True:
            errors.append(f"cell_{index}_repeat_consistency")
            parity = False
        if cell.get("invalidated_frames") != sum(v >= 100 for v in oracle):
            errors.append(f"cell_{index}_invalidated")
        if cell.get("unchanged_frames") != sum(v < 100 for v in oracle):
            errors.append(f"cell_{index}_unchanged")
        cpu = cell.get("cpu_times_ms")
        cuda = cell.get("cuda_times_ms")
        orders = cell.get("orders")
        if not all(isinstance(v, list) and len(v) == 21 for v in (cpu, cuda, orders)):
            errors.append(f"cell_{index}_timing_cardinality")
            continue
        if not all(isinstance(t, (int, float)) and math.isfinite(t) and t >= 0 for t in cpu + cuda):
            errors.append(f"cell_{index}_timing_value")
            continue
        expected_orders = ["cpu_then_cuda" if i % 2 == 0 else "cuda_then_cpu" for i in range(21)]
        if orders != expected_orders:
            errors.append(f"cell_{index}_order")
        cm = statistics.median(cpu)
        gm = statistics.median(cuda)
        cp = sorted(cpu)[19]
        gp = sorted(cuda)[19]
        if cell.get("cpu_median_ms") != cm or cell.get("cuda_median_ms") != gm:
            errors.append(f"cell_{index}_median")
        if cell.get("cpu_p95_ms") != cp or cell.get("cuda_p95_ms") != gp:
            errors.append(f"cell_{index}_p95")
        ratio = gm / cm if cm else None
        if cell.get("cuda_over_cpu_median") != ratio:
            errors.append(f"cell_{index}_ratio")
        if cell.get("gpu_break_even_observed") != (gm < cm):
            errors.append(f"cell_{index}_break_even")
        seen.append(key)

    if raw.get("parity") is not parity:
        errors.append("parity_summary")
    expected_status = "FAIL_GPU_CPU_PARITY" if not parity else "DIAGNOSTIC_COMPLETE"
    if raw.get("status") != expected_status:
        errors.append("status")
    break_even_cells = sum(1 for cell in cells if isinstance(cell, dict) and cell.get("gpu_break_even_observed") is True)
    scientific_result = ("FAIL_GPU_CPU_PARITY" if not parity else "GPU_SPEEDUP_OBSERVED_IN_SCOPED_CELLS" if break_even_cells else "GPU_SPEEDUP_NOT_ESTABLISHED")
    audit_status = "PASS_RAW_AUDIT" if not errors else "FAIL_RAW_AUDIT"
    print(json.dumps({"status": audit_status, "scientific_result": scientific_result, "break_even_cells": break_even_cells, "audited_cells": len(seen), "raw_sha256": hashlib.sha256(raw_bytes).hexdigest(), "errors": errors}, sort_keys=True, separators=(",", ":")))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
