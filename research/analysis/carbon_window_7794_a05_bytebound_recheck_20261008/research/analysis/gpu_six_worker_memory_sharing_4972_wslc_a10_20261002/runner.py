#!/usr/bin/env python3
"""One-shot six-worker CUDA coexistence candidate for the WSLc allocation."""
from __future__ import annotations

import csv
import json
import multiprocessing as mp
import os
import queue
import sys
import time
from pathlib import Path

ALLOCATION = "GPU-MEMORY-SHARING-4972-20261002-10"
SEED = 49720261010
WORKERS = 6
NUMEL = 24 * 1024 * 1024
WORKING_BYTES = NUMEL * 8
OPS = 20
ALLOCATOR_FRACTION = 0.05
EXPECTED_DEVICE = "NVIDIA GeForce RTX 3080 Laptop GPU"
MIN_INITIAL_FREE = 10 * 1024**3
MIN_GLOBAL_FREE = 4 * 1024**3
OUT = Path(os.environ.get("GPU_A10_OUTPUT", "/out"))


def worker(worker_id: int, barrier, results) -> None:
    row = {"worker_id": worker_id, "pid": os.getpid(), "seed": SEED, "status": "error"}
    try:
        import torch

        torch.cuda.set_device(0)
        properties = torch.cuda.get_device_properties(0)
        torch.cuda.set_per_process_memory_fraction(ALLOCATOR_FRACTION, 0)
        total_before, free_before = torch.cuda.mem_get_info(0)
        start = (SEED % 997) + worker_id * 11
        values = torch.full((NUMEL,), start, dtype=torch.int64, device="cuda:0")
        torch.cuda.synchronize(0)
        allocated = torch.cuda.memory_allocated(0)
        peak = torch.cuda.max_memory_allocated(0)
        barrier.wait(timeout=45)
        total_overlap, free_overlap = torch.cuda.mem_get_info(0)
        for _ in range(OPS):
            values.add_(1)
        torch.cuda.synchronize(0)
        checksum = int(values.sum().item())
        expected = NUMEL * (start + OPS)
        _, free_after = torch.cuda.mem_get_info(0)
        row.update({
            "status": "ok" if checksum == expected else "checksum_mismatch",
            "device": properties.name,
            "device_total_bytes": int(total_overlap),
            "global_free_before_bytes": int(free_before),
            "global_free_overlap_bytes": int(free_overlap),
            "global_free_after_bytes": int(free_after),
            "allocated_bytes": int(allocated),
            "peak_allocated_bytes": int(peak),
            "reserved_bytes": int(torch.cuda.memory_reserved(0)),
            "numel": NUMEL,
            "ops": OPS,
            "initial_value": start,
            "checksum": checksum,
            "expected_checksum": expected,
        })
        del values
        torch.cuda.synchronize(0)
    except BaseException as exc:
        row["error"] = f"{type(exc).__name__}: {exc}"
    finally:
        results.put(row)


def _read_samples(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: runner.py /samples/host_gpu_samples.csv", file=sys.stderr)
        return 2
    samples_path = Path(sys.argv[1])
    OUT.mkdir(parents=True, exist_ok=True)
    names = ("candidate.jsonl", "candidate_summary.json", "audit.json")
    if any((OUT / name).exists() for name in names):
        raise SystemExit("fresh output directory required; candidate artifacts already exist")
    if not samples_path.is_file():
        raise SystemExit("independent host GPU telemetry file is absent")
    rows: list[dict] = []
    exitcodes: list[int | None] = []
    gate_error = None
    try:
        baseline = _read_samples(samples_path)
        if not baseline:
            gate_error = "independent host telemetry has no baseline row"
        else:
            initial_free = int(float(baseline[0]["memory_free_mib"]) * 1024**2)
            if initial_free < MIN_INITIAL_FREE:
                gate_error = "initial global free VRAM below 10 GiB"

        if not gate_error:
            context = mp.get_context("spawn")
            barrier = context.Barrier(WORKERS)
            results = context.Queue()
            children = [
                context.Process(target=worker, args=(index, barrier, results), name=f"gpu-a10-{index}")
                for index in range(WORKERS)
            ]
            for process in children:
                process.start()
            deadline = time.monotonic() + 110
            while len(rows) < WORKERS and time.monotonic() < deadline:
                try:
                    rows.append(results.get(timeout=1))
                except queue.Empty:
                    if all(not process.is_alive() for process in children):
                        break
            for process in children:
                process.join(timeout=max(0.0, deadline - time.monotonic()))
            for process in children:
                if process.is_alive():
                    process.terminate()
                    process.join(timeout=3)
            exitcodes = [process.exitcode for process in children]
    except BaseException as exc:
        gate_error = f"{type(exc).__name__}: {exc}"

    rows.sort(key=lambda item: item.get("worker_id", -1))
    with (OUT / "candidate.jsonl").open("w", encoding="utf-8", newline="\n") as stream:
        for row in rows:
            stream.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")
    samples = _read_samples(samples_path)
    free_values = []
    try:
        free_values = [int(float(item["memory_free_mib"]) * 1024**2) for item in samples]
    except Exception:
        pass
    workers_ok = len(rows) == WORKERS and all(item.get("status") == "ok" for item in rows)
    sampler_ok = len(samples) >= 2 and bool(free_values) and min(free_values) >= MIN_GLOBAL_FREE
    success = workers_ok and all(code == 0 for code in exitcodes) and sampler_ok and gate_error is None
    summary = {
        "schema": "gpu-a10-candidate-v1",
        "allocation": ALLOCATION,
        "seed": SEED,
        "workers_expected": WORKERS,
        "workers_recorded": len(rows),
        "worker_exitcodes": exitcodes,
        "host_samples_observed_during_candidate": len(samples),
        "host_free_min_bytes_observed_during_candidate": min(free_values) if free_values else None,
        "gate_error": gate_error,
        "candidate_exit_ok": success,
    }
    (OUT / "candidate_summary.json").write_text(json.dumps(summary, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, sort_keys=True))
    return 0 if success else 2


if __name__ == "__main__":
    raise SystemExit(main())
