"""One-shot exact host-frame CPU vs CUDA benchmark for Issue #4957."""
from __future__ import annotations
import hashlib
import json
import math
import os
import platform
import statistics
import sys
import time
from datetime import datetime, timezone

import numpy as np
import torch

ALLOCATION = "gpu-exact-frame-gate-1564-20260928-01"
SIZES = [(64, 64), (1920, 1080), (3840, 2160)]
REPEATS = 25
WARMUPS = 3
DEVICE = "cuda:0"

def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def make_pair(width: int, height: int, seed: int):
    rng = np.random.default_rng(seed)
    a = rng.integers(0, 256, size=(height, width, 4), dtype=np.uint8)
    a = np.ascontiguousarray(a)
    same = a.copy()
    changed = a.copy()
    changed[height // 2, width // 2, 0] ^= np.uint8(1)
    return a, {"UNCHANGED": same, "ONE_CHANNEL_PIXEL_CHANGE": changed}

def cpu_equal(a, b):
    return bool(np.array_equal(a, b))

def cuda_equal(a, b):
    ta = torch.from_numpy(a).to(DEVICE, non_blocking=False)
    tb = torch.from_numpy(b).to(DEVICE, non_blocking=False)
    equal = bool(torch.equal(ta, tb))
    torch.cuda.synchronize()
    return equal

def percentile95(values):
    ordered = sorted(values)
    return ordered[math.ceil(0.95 * len(ordered)) - 1]

def timed(fn, a, b):
    start = time.perf_counter_ns()
    result = fn(a, b)
    elapsed = time.perf_counter_ns() - start
    return result, elapsed

def main():
    if not torch.cuda.is_available():
        raise RuntimeError("CUDA_NOT_AVAILABLE")
    if torch.cuda.device_count() < 1:
        raise RuntimeError("CUDA_DEVICE_COUNT_ZERO")
    torch.cuda.set_device(0)
    device_name = torch.cuda.get_device_name(0)
    torch.cuda.init()
    torch.cuda.synchronize()

    cases = []
    measurements = []
    for size_index, (width, height) in enumerate(SIZES):
        a, outcomes = make_pair(width, height, seed=156400 + size_index)
        for outcome_index, (outcome, b) in enumerate(outcomes.items()):
            expected = outcome == "UNCHANGED"
            cpu_answer = cpu_equal(a, b)
            cuda_answer = cuda_equal(a, b)
            cases.append({
                "width": width,
                "height": height,
                "channels": 4,
                "outcome": outcome,
                "expected_equal": expected,
                "cpu_equal": cpu_answer,
                "cuda_equal": cuda_answer,
                "input_pair_sha256": sha256(a.tobytes(order="C") + b.tobytes(order="C")),
            })
            if cpu_answer != expected or cuda_answer != expected:
                raise RuntimeError("EXACTNESS_GATE_FAILED")

            # Warm both paths before timing; warm-up durations are not retained.
            for _ in range(WARMUPS):
                cpu_equal(a, b)
                cuda_equal(a, b)

            cpu_ns, cuda_ns = [], []
            for pair_index in range(REPEATS):
                order = ("CPU", "CUDA") if pair_index % 2 == 0 else ("CUDA", "CPU")
                for arm in order:
                    fn = cpu_equal if arm == "CPU" else cuda_equal
                    answer, elapsed = timed(fn, a, b)
                    if answer != expected:
                        raise RuntimeError("TIMED_EXACTNESS_GATE_FAILED")
                    (cpu_ns if arm == "CPU" else cuda_ns).append(elapsed)
            measurements.append({
                "width": width,
                "height": height,
                "outcome": outcome,
                "repeats_per_arm": REPEATS,
                "cpu_ns": cpu_ns,
                "cuda_end_to_end_ns": cuda_ns,
                "cpu_median_ns": int(statistics.median(cpu_ns)),
                "cuda_end_to_end_median_ns": int(statistics.median(cuda_ns)),
                "cpu_p95_ns": int(percentile95(cpu_ns)),
                "cuda_end_to_end_p95_ns": int(percentile95(cuda_ns)),
            })

    large_wins = all(
        next(m for m in measurements if (m["width"], m["height"], m["outcome"]) == (w, h, "UNCHANGED"))["cuda_end_to_end_median_ns"]
        < next(m for m in measurements if (m["width"], m["height"], m["outcome"]) == (w, h, "UNCHANGED"))["cpu_median_ns"]
        for w, h in [(1920, 1080), (3840, 2160)]
    )
    result = {
        "schema_version": 1,
        "allocation": ALLOCATION,
        "started_utc": datetime.now(timezone.utc).isoformat(),
        "host": {
            "platform": platform.platform(),
            "python": sys.version,
            "numpy": np.__version__,
            "pytorch": torch.__version__,
            "torch_cuda_runtime": torch.version.cuda,
            "nvidia_driver_version": os.environ.get("NVIDIA_DRIVER_VERSION"),
            "device": device_name,
            "device_count": torch.cuda.device_count(),
        },
        "source_sha256": sha256(__import__("pathlib").Path(__file__).read_bytes()),
        "warmups_per_case_per_arm": WARMUPS,
        "repeats_per_arm": REPEATS,
        "exactness_cases": cases,
        "measurements": measurements,
        "large_size_cuda_wins_on_unchanged": large_wins,
        "decision": "PASS_GPU_EXACT_GATE_BREAK_EVEN_SCOPED" if large_wins else "REJECT_GPU_FOR_HOST_RESIDENT_EXACT_O1_SCOPED",
    }
    with open("result.json", "w", encoding="utf-8", newline="\n") as f:
        json.dump(result, f, sort_keys=True, indent=2, allow_nan=False)
        f.write("\n")
    print(json.dumps({
        "allocation": ALLOCATION,
        "decision": result["decision"],
        "device": device_name,
        "measurements": [
            {k: m[k] for k in ("width", "height", "outcome", "cpu_median_ns", "cuda_end_to_end_median_ns", "cpu_p95_ns", "cuda_end_to_end_p95_ns")}
            for m in measurements
        ],
    }, sort_keys=True))

if __name__ == "__main__":
    main()
