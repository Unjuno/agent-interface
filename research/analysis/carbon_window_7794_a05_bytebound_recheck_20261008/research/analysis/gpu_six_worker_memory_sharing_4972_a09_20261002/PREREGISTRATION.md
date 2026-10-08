# Preregistration — allocation GPU-MEMORY-SHARING-4972-20261002-09

Issue: #6329. Fresh successor after #6319's pre-candidate allocation/seed collision STOP. Preserve #6319 and #6322 unchanged. #6308's exclusive transfer-inclusive timing design remains unmodified.

Base main SHA: 8d9b496dd23b72bf73ca06756e23c329f5489735
Branch: research/gpu-six-worker-memory-sharing-4972-a09b-20261002
Evidence path: research/analysis/gpu_six_worker_memory_sharing_4972_a09_20261002/

## Hypothesis
Six bounded independent Python/PyTorch processes can concurrently allocate and use a fixed CUDA working set on the host RTX 3080, rendezvous while all allocations remain live, and produce exact independently reconstructable integer checksums without OOM or device loss.

## Frozen treatment
- Fresh seed: 49720261009.
- Workers: 6 independent spawned processes, each on CUDA device 0.
- Working set: one 24*1024*1024 element int64 tensor per worker (exactly 192 MiB).
- Per-process PyTorch caching-allocator fraction: 0.05 of total VRAM.
- Operations: 20 in-place integer increments after a six-way allocation barrier.
- Pinned image: pytorch/pytorch@sha256:831247999fbf7e08f61b3e39f6d77ee434f38f6f07f769d00db451e853878067, linux/amd64.
- Runtime: WSL Arch + rootful Podman/crun + NVIDIA CDI, offline, no image pull/build, read-only source/root, fresh output.

## Start gate
Use fresh current-main/source/freeze identities. Require exact image digest already present, correct RTX 3080/CUDA visibility, unique absent output, stable host/WSL capacity, and free VRAM >=10 GiB before launch. Inspect process/container ownership and record current GPU memory/utilization. Any unknown owner, failed preflight, image acquisition need, or capacity below threshold => typed pre-candidate STOP; candidate=0. This allocation is explicitly a controlled six-process shared-memory probe; no external job is assumed harmless. If a known external workload is active, record it and require free VRAM >=10 GiB before launch and >=4 GiB throughout. Do not stop or modify any other process/container.

## Invocation and audit
At most one candidate container invocation. At most one separate raw-only CPU audit, only after candidate exit 0. The audit reconstructs six checksums from constants and checks the full host GPU CSV telemetry interval. No retry, replacement, download, or seed substitution.

## Decision
PASS only when all six unique workers report the exact device, exactly 192 MiB allocated, complete all 20 operations, match independent integer checksum reconstruction, exit cleanly, and report synchronized global free VRAM >=4 GiB. The host sampler's first row must show >=10 GiB free and every row >=4 GiB. Aggregate worker allocator peak must be <=8 GiB. Missing/duplicate/malformed rows, corruption, or checksum mismatch => FAIL/HOLD. OOM/device loss => typed resource STOP/FAIL, never PASS. This is not a latency/throughput experiment.

## Scope limits
One laptop, one CUDA runtime, one synthetic integer workload and one six-process configuration. Allocator metrics do not include all driver/context memory; global free memory is separately recorded. No claim about arbitrary model memory, six full AI agents, training safety, production behavior, or performance benefit.
