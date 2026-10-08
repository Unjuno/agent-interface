# #59 GPU ROI transfer-cost diagnostic preregistration

Allocation: `MAP01-ROI-BREAK-EVEN-59-GPU-20261001-01`  
Branch: `research/doom-gpu-roi-break-even-20261001-01`  
Source main: `d2567fe0999136fc351d1728b94586c457b0d9d3`  
Window: 2026-10-01 03:05–03:15 UTC (local Windows RTX 3080 Laptop only)

## H / T / D / C / U

- **H:** For the exact one-way changed-pixel metric used by #5118, CUDA including host↔device transfers and synchronization exactly matches an independent NumPy CPU oracle. End-to-end latency may cross over at larger ROI/batch sizes. This tests only whether GPU execution is computationally plausible for frequent evidence sampling.
- **T:** One bounded invocation on deterministic synthetic uint8 RGB pairs. ROI dimensions 95×50, 320×200, 640×400, 1280×800; batch sizes 1, 4, 16. Frozen metric: a pixel changes iff max absolute RGB-channel delta >32; a frame is INVALIDATED iff changed pixels >=100. Three warmups and 21 timed repeats per arm/cell; alternating CPU-first/GPU-first order. GPU time includes both H2D transfers, cast/delta/reduction, synchronization, and D2H result. Inputs/fixture generation are outside timing.
- **D:** Retain per-cell per-repeat end-to-end wall times and exact per-frame CPU/CUDA count vectors. Any count mismatch => `FAIL_GPU_CPU_PARITY`; do not tune or retry. Report median and p95 CPU/CUDA time ratios. A break-even is observed only where CUDA median < CPU median; else `GPU_SPEEDUP_NOT_ESTABLISHED`. Missing CUDA/device/source/lease gate => STOP before benchmark tensors are evaluated. This is one diagnostic sweep, not performance qualification.
- **C:** Windows host, installed PyTorch CUDA and NumPy; RTX 3080 Laptop. Synthetic frames; timing is sensitive to OS/GPU load and tensor allocation. Batch max 16 bounds fixture memory.
- **U:** No retained real frames, task/effect oracle, threat recognition, live-control, safety, production, or MAP01 outcome claim. The prior #5118 result (13 postselected 95×50 frames, exact parity, 140.148 ms total) remains unchanged and did not show speedup.

## Execution gates

Before the one invocation, recheck the allocation window, owner/task overlap, and `nvidia-smi` workload. Stop without evaluating inputs if another CUDA workload is present, CUDA unavailable, or the exact frozen hashes differ. Invocation command:

```powershell
python -B benchmark.py
```

The benchmark is self-contained and imports no project code; its additive branch may be based on an earlier commit, while this source-main pin records the repository state at allocation freeze. The single stdout JSON is the raw record. The independent auditor will parse that retained raw once, regenerate deterministic fixtures from the pinned seed/config, verify every fixture digest and all 21 CPU/CUDA per-frame count vectors against an independent NumPy oracle, then recompute timing summaries and check cardinality. No retrials, threshold changes, warmed data edits, or performance tuning are allowed after invocation.