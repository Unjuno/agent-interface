#!/usr/bin/env python3
"""One-shot six-process bounded CUDA memory-sharing candidate."""
from __future__ import annotations

import json
import multiprocessing as mp
import os
import queue
import time
from pathlib import Path

SEED = 49720261008
WORKERS = 6
NUMEL = 24 * 1024 * 1024
WORKING_BYTES = NUMEL * 8
OPS = 20
ALLOCATOR_FRACTION = 0.05
EXPECTED_DEVICE = "NVIDIA GeForce RTX 3080 Laptop GPU"
OUT = Path(os.environ.get("GPU_A08_OUTPUT", "/out"))


def worker(worker_id: int, barrier, results) -> None:
    row = {
        "worker_id": worker_id,
        "pid": os.getpid(),
        "seed": SEED,
        "status": "error",
    }
    try:
        import torch

        torch.cuda.set_device(0)
        torch.cuda.set_per_process_memory_fraction(ALLOCATOR_FRACTION, 0)
        props = torch.cuda.get_device_properties(0)
        total_before, free_before = torch.cuda.mem_get_info(0)
        initial = (SEED % 997) + worker_id * 11
        tensor = torch.full((NUMEL,), initial, dtype=torch.int64, device="cuda:0")
        torch.cuda.synchronize(0)
        allocated = torch.cuda.memory_allocated(0)
        peak_allocated = torch.cuda.max_memory_allocated(0)
        barrier.wait(timeout=45)
        total_overlap, free_overlap = torch.cuda.mem_get_info(0)
        for _ in range(OPS):
            tensor.add_(1)
        torch.cuda.synchronize(0)
        checksum = int(tensor.sum().item())
        expected = NUMEL * (initial + OPS)
        total_after, free_after = torch.cuda.mem_get_info(0)
        row.update({
            "status": "ok" if checksum == expected else "checksum_mismatch",
            "device": props.name,
            "device_total_bytes": int(total_overlap),
            "global_free_before_bytes": int(free_before),
            "global_free_overlap_bytes": int(free_overlap),
            "global_free_after_bytes": int(free_after),
            "allocated_bytes": int(allocated),
            "peak_allocated_bytes": int(peak_allocated),
            "reserved_bytes": int(torch.cuda.memory_reserved(0)),
            "numel": NUMEL,
            "ops": OPS,
            "initial_value": initial,
            "checksum": checksum,
            "expected_checksum": expected,
        })
        del tensor
        torch.cuda.synchronize(0)
    except BaseException as exc:
        row["error"] = f"{type(exc).__name__}: {exc}"
        row["status"] = "error"
    finally:
        results.put(row)


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    if any(OUT.iterdir()):
        raise SystemExit("output directory must be empty")
    ctx = mp.get_context("spawn")
    barrier = ctx.Barrier(WORKERS)
    results = ctx.Queue()
    children = [
        ctx.Process(target=worker, args=(worker_id, barrier, results), name=f"gpu-a08-{worker_id}")
        for worker_id in range(WORKERS)
    ]
    for process in children:
        process.start()

    deadline = time.monotonic() + 100
    rows = []
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

    rows.sort(key=lambda row: row.get("worker_id", -1))
    with (OUT / "candidate.jsonl").open("w", encoding="utf-8", newline="\n") as stream:
        for row in rows:
            stream.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")
    summary = {
        "allocation": "GPU-MEMORY-SHARING-4972-20261002-08",
        "seed": SEED,
        "workers_expected": WORKERS,
        "workers_recorded": len(rows),
        "exitcodes": [process.exitcode for process in children],
        "candidate_exit_ok": len(rows) == WORKERS and all(
            row.get("status") == "ok" for row in rows
        ) and all(process.exitcode == 0 for process in children),
    }
    (OUT / "candidate_summary.json").write_text(
        json.dumps(summary, sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )
    return 0 if summary["candidate_exit_ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
