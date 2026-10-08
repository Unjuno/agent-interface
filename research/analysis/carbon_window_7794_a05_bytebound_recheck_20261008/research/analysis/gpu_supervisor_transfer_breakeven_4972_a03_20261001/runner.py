#!/usr/bin/env python3
"""One-shot, transfer-inclusive CPU/CUDA hint cost study; synthetic data only."""
import hashlib
import json
import platform
import statistics
import sys
import time
from pathlib import Path

import torch

ROOT = Path(__file__).resolve().parent
THRESHOLD = 700
BATCH_SIZES = (1, 4, 16, 64, 256, 1024)
WARMUPS = 5
REPEATS = 30


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def cpu_route(rows):
    hints = [int(row["confidence_milli"] >= THRESHOLD) for row in rows]
    admitted = [int(h and row["observed_sequence"] == row["current_sequence"]
                    and row["ambiguous"] is False and row["forced_yield"] is False)
                for row, h in zip(rows, hints)]
    return hints, admitted


def gpu_route(rows, device):
    # Include host-list extraction, host tensor construction and H2D transfer.
    confidence = torch.tensor([row["confidence_milli"] for row in rows], dtype=torch.int32)
    current = torch.tensor([row["current_sequence"] for row in rows], dtype=torch.int64)
    observed = torch.tensor([row["observed_sequence"] for row in rows], dtype=torch.int64)
    ambiguous = torch.tensor([row["ambiguous"] for row in rows], dtype=torch.bool)
    forced = torch.tensor([row["forced_yield"] for row in rows], dtype=torch.bool)
    tensors = [v.to(device, non_blocking=False) for v in
               (confidence, current, observed, ambiguous, forced)]
    confidence, current, observed, ambiguous, forced = tensors
    hints = confidence.ge(THRESHOLD)
    # The final gate intentionally remains CPU-owned; include D2H and that gate.
    hint_list = hints.to("cpu").to(torch.int8).tolist()
    current_list = current.to("cpu").tolist()
    observed_list = observed.to("cpu").tolist()
    ambiguous_list = ambiguous.to("cpu").tolist()
    forced_list = forced.to("cpu").tolist()
    admitted = [int(h and o == c and not a and not f)
                for h, o, c, a, f in zip(hint_list, observed_list, current_list,
                                         ambiguous_list, forced_list)]
    torch.cuda.synchronize(device)
    return [int(v) for v in hint_list], admitted


def timed(fn):
    start = time.perf_counter_ns()
    value = fn()
    elapsed = time.perf_counter_ns() - start
    return value, elapsed


def main():
    data_path = ROOT / "dataset.json"
    freeze_path = ROOT / "FREEZE.json"
    if not data_path.is_file() or not freeze_path.is_file():
        raise SystemExit("STOP: frozen inputs missing")
    freeze = json.loads(freeze_path.read_text(encoding="utf-8"))
    if (sha(Path(__file__)) != freeze["runner_sha256"] or sha(data_path) != freeze["dataset_sha256"]
            or sha(ROOT / "prepare.py") != freeze["prepare_sha256"]):
        raise SystemExit("STOP: source/data hash mismatch")
    doc = json.loads(data_path.read_text(encoding="utf-8"))
    rows = doc["rows"]
    if len(rows) != 1024:
        raise SystemExit("STOP: dataset row count")
    if not torch.cuda.is_available():
        raise SystemExit("STOP: CUDA unavailable")
    if (sys.version_info[:2] != (3, 11) or torch.__version__ != "2.5.1+cu121"
            or torch.version.cuda != "12.1" or torch.cuda.get_device_name(0) != "NVIDIA GeForce RTX 3080 Laptop GPU"):
        raise SystemExit("STOP: runtime identity differs from frozen host")
    device = torch.device("cuda:0")
    torch.cuda.init()
    # Warm both routes before measured paired samples.
    for size in BATCH_SIZES:
        subset = rows[:size]
        for _ in range(WARMUPS):
            cpu_route(subset)
            gpu_route(subset, device)
    torch.cuda.synchronize(device)

    timing = {str(size): {"cpu_ns": [], "cuda_end_to_end_ns": []} for size in BATCH_SIZES}
    raw = {str(size): [] for size in BATCH_SIZES}
    for rep in range(REPEATS):
        for size in BATCH_SIZES:
            subset = rows[:size]
            order = ("cpu", "cuda") if rep % 2 == 0 else ("cuda", "cpu")
            results = {}
            for route in order:
                if route == "cpu":
                    (hints, admitted), elapsed = timed(lambda: cpu_route(subset))
                    timing[str(size)]["cpu_ns"].append(elapsed)
                else:
                    (hints, admitted), elapsed = timed(lambda: gpu_route(subset, device))
                    timing[str(size)]["cuda_end_to_end_ns"].append(elapsed)
                results[route] = (hints, admitted)
            cpu_h, cpu_a = results["cpu"]
            gpu_h, gpu_a = results["cuda"]
            raw[str(size)].append({"rep": rep, "order": list(order),
                                   "cpu_hint": cpu_h, "cuda_hint": gpu_h,
                                   "cpu_admitted": cpu_a, "cuda_admitted": gpu_a})

    result = {
        "schema": "gpu-supervisor-transfer-break-even-result-v1",
        "allocation": freeze["allocation"], "base_main_sha": freeze["base_main_sha"],
        "dataset_sha256": sha(data_path),
        "source_sha256": {"prepare": sha(ROOT / "prepare.py"), "runner": sha(Path(__file__))},
        "environment": {"python": sys.version, "platform": platform.platform(),
                        "torch": torch.__version__, "cuda_runtime": torch.version.cuda,
                        "device": torch.cuda.get_device_name(device)},
        "threshold_milli": THRESHOLD, "row_count": len(rows),
        "stratum_counts": {name: sum(r["stratum"] == name for r in rows)
                           for name in ("fresh_valid", "stale", "ambiguous", "forced_yield")},
        "batch_sizes": list(BATCH_SIZES), "warmups_per_route_size": WARMUPS,
        "paired_repetitions": REPEATS, "timing_ns": timing, "raw_pairs": raw,
        "p50_ns": {str(size): {
            "cpu": statistics.median(timing[str(size)]["cpu_ns"]),
            "cuda_end_to_end": statistics.median(timing[str(size)]["cuda_end_to_end_ns"])}
            for size in BATCH_SIZES},
        "disposition": "RAW_EMITTED_AWAITING_INDEPENDENT_CPU_AUDIT",
    }
    out = ROOT / "candidate_result.json"
    if out.exists():
        raise SystemExit("STOP: candidate output already exists")
    out.write_text(json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    print(json.dumps({"rows": len(rows), "sizes": len(BATCH_SIZES),
                      "disposition": result["disposition"]}, sort_keys=True))


if __name__ == "__main__":
    main()

