import hashlib
import json
import math
import platform
import sys
import time
from pathlib import Path

import numpy as np
import torch


WIDTH_HEIGHT = [(95, 50), (320, 200), (640, 400), (1280, 800)]
BATCHES = [1, 4, 16]
WARMUPS = 3
REPEATS = 21
SEED = 59020261001
DELTA_THRESHOLD = 32
MIN_CHANGED_PIXELS = 100


def cpu_counts(before: np.ndarray, after: np.ndarray) -> list[int]:
    delta = np.abs(before.astype(np.int16) - after.astype(np.int16))
    changed = np.max(delta, axis=-1) > DELTA_THRESHOLD
    return changed.sum(axis=(-2, -1), dtype=np.int64).tolist()


def cuda_counts(before: np.ndarray, after: np.ndarray, device: str) -> list[int]:
    a = torch.from_numpy(before).to(device=device, dtype=torch.int16)
    b = torch.from_numpy(after).to(device=device, dtype=torch.int16)
    counts = (torch.amax(torch.abs(a - b), dim=-1) > DELTA_THRESHOLD).sum(dim=(-2, -1))
    torch.cuda.synchronize()
    return counts.cpu().numpy().astype(np.int64).tolist()


def elapsed(fn) -> tuple[float, list[int]]:
    start = time.perf_counter_ns()
    result = fn()
    duration_ms = (time.perf_counter_ns() - start) / 1_000_000
    return duration_ms, result


def percentile95(values: list[float]) -> float:
    ordered = sorted(values)
    return ordered[max(0, math.ceil(0.95 * len(ordered)) - 1)]


def main() -> int:
    if not torch.cuda.is_available():
        print(json.dumps({"status": "STOP_CUDA_UNAVAILABLE"}, sort_keys=True))
        return 2

    device = "cuda:0"
    rng = np.random.default_rng(SEED)
    cells = []
    parity_failure = False

    for width, height in WIDTH_HEIGHT:
        for batch in BATCHES:
            before = rng.integers(0, 256, size=(batch, height, width, 3), dtype=np.uint8)
            after = rng.integers(0, 256, size=(batch, height, width, 3), dtype=np.uint8)
            fixture_sha = hashlib.sha256(before.tobytes() + after.tobytes()).hexdigest()

            for _ in range(WARMUPS):
                warm_cpu = cpu_counts(before, after)
                warm_gpu = cuda_counts(before, after, device)
                if warm_cpu != warm_gpu:
                    parity_failure = True

            cpu_times: list[float] = []
            cuda_times: list[float] = []
            cpu_rows: list[list[int]] = []
            cuda_rows: list[list[int]] = []
            orders: list[str] = []

            for i in range(REPEATS):
                if i % 2 == 0:
                    order = "cpu_then_cuda"
                    cpu_ms, c = elapsed(lambda: cpu_counts(before, after))
                    cuda_ms, g = elapsed(lambda: cuda_counts(before, after, device))
                else:
                    order = "cuda_then_cpu"
                    cuda_ms, g = elapsed(lambda: cuda_counts(before, after, device))
                    cpu_ms, c = elapsed(lambda: cpu_counts(before, after))
                cpu_times.append(cpu_ms)
                cuda_times.append(cuda_ms)
                cpu_rows.append(c)
                cuda_rows.append(g)
                orders.append(order)
                if c != g:
                    parity_failure = True

            cpu_median = float(np.median(cpu_times))
            cuda_median = float(np.median(cuda_times))
            cells.append(
                {
                    "width": width,
                    "height": height,
                    "batch": batch,
                    "fixture_sha256": fixture_sha,
                    "cpu_counts": cpu_rows[0],
                    "cuda_counts": cuda_rows[0],
                    "cpu_rows": cpu_rows,
                    "cuda_rows": cuda_rows,
                    "cpu_rows_all_match": all(row == cpu_rows[0] for row in cpu_rows),
                    "cuda_rows_all_match": all(row == cuda_rows[0] for row in cuda_rows),
                    "cpu_times_ms": cpu_times,
                    "cuda_times_ms": cuda_times,
                    "orders": orders,
                    "cpu_median_ms": cpu_median,
                    "cuda_median_ms": cuda_median,
                    "cpu_p95_ms": percentile95(cpu_times),
                    "cuda_p95_ms": percentile95(cuda_times),
                    "cuda_over_cpu_median": cuda_median / cpu_median if cpu_median else None,
                    "gpu_break_even_observed": cuda_median < cpu_median,
                    "invalidated_frames": sum(v >= MIN_CHANGED_PIXELS for v in cpu_rows[0]),
                    "unchanged_frames": sum(v < MIN_CHANGED_PIXELS for v in cpu_rows[0]),
                }
            )

    source_sha = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    result = {
        "schema": "map01-roi-gpu-break-even-raw-v1",
        "allocation": "MAP01-ROI-BREAK-EVEN-59-GPU-20261001-01",
        "status": "FAIL_GPU_CPU_PARITY" if parity_failure else "DIAGNOSTIC_COMPLETE",
        "parity": not parity_failure,
        "thresholds": {"channel_max_delta_exclusive": DELTA_THRESHOLD, "changed_pixels_minimum_inclusive": MIN_CHANGED_PIXELS},
        "config": {"dimensions_wh": WIDTH_HEIGHT, "batches": BATCHES, "warmups": WARMUPS, "repeats": REPEATS, "seed": SEED},
        "environment": {
            "python": sys.version,
            "platform": platform.platform(),
            "numpy": np.__version__,
            "torch": torch.__version__,
            "torch_cuda": torch.version.cuda,
            "device": torch.cuda.get_device_name(0),
        },
        "source_sha256": source_sha,
        "cell_count": len(cells),
        "cells": cells,
        "scope": "synthetic offline timing; no live game/model/GUI/input or task-effect claim",
    }
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0 if not parity_failure else 1


if __name__ == "__main__":
    raise SystemExit(main())
