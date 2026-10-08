# Allocation-08 preregistration

Issue #6322; fresh successor to #5882 allocation-06's terminal pre-candidate capacity STOP. Preserve all earlier allocations, including pending Docker allocation-07, unchanged. User directed execution inside a WSL container; this package uses a fresh allocation and seed.

## H / T / D / C / U

**H.** For confidence-only CONTINUE/YIELD hints with a CPU-owned final gate, transfer-inclusive CUDA could be at least 20% faster per row only at larger batches. If no size clears that threshold, CPU remains preferred for this synthetic workload.

**T.** Allocation GPU-SUPERVISOR-TRANSFER-BREAK-EVEN-4972-20261002-08; seed 49720261008; 1,024 fresh typed rows (256 each in fresh_valid, stale, ambiguous, forced_yield); batch sizes 1,4,16,64,256,1024; five warmups and 30 alternating paired repetitions. Runtime: one RTX 3080 Laptop GPU passed into an Arch Linux WSL 2 Podman rootful/crun container through NVIDIA CDI; image pytorch/pytorch@sha256:831247999fbf7e08f61b3e39f6d77ee434f38f6f07f769d00db451e853878067 (linux/amd64). Proposed exclusive interval 2026-10-02 00:45–01:00 UTC, after #6296/#6308 owner windows and explicit release. One candidate; only if it exits 0, one separate raw-only CPU auditor. No retries/substitute seed. Pull and verify image before the formal slot; formal containers run with network disabled.

**D.** Exact CPU/CUDA hint and CPU-owned admission parity for every sampled prefix; no stale, ambiguous or forced-yield admission; reconstruct all rows, 30 timings per route/size, and medians; reject all six corruption controls. If integrity passes and CUDA median end-to-end latency per row is at least 20% lower at any tested size, report PASS_TRANSFER_INCLUSIVE_GPU_CROSSOVER_SCOPED and first qualifying size. Otherwise report PASS_CPU_PREFERRED_NO_GPU_CROSSOVER_SCOPED. Contract mismatch => FAIL; audit/provenance defect => HOLD; queue, runtime, or capacity gate => terminal STOP with zero candidate.

**C.** One Windows laptop/RTX 3080, Arch WSL 2, Podman 6.1.3, crun, NVIDIA Container Toolkit 1.20.0/CDI, pinned linux/amd64 image, synthetic data, and host load/thermal conditions. CUDA only emits a hint; the final gate remains CPU-owned.

**U.** Synthetic hint microbenchmark only. It does not establish natural batch-size prevalence, model-call savings, GUI/game behavior, safety, task success, production authority, cross-device speed, or end-to-end Agent Interface benefit.

## Start gate

At the requested interval, refresh #5085 and all active owners; require explicit completion/release of prior owner-bound allocations and no overlap. Re-fetch main; synchronize/freeze if it changed. Check exact source/data/freeze/image hashes, Podman running-container inventory, image platform/digest, generated CDI device nvidia.com/gpu=all, empty output path, RTX 3080 identity/idle state, no compute processes, and two WSL-root free-space readings at least 60 seconds apart, each >=1 GiB and nondecreasing. Any unresolved owner, missing grant/release, discrepancy, or failed gate is STOP before candidate. Candidate and auditor each have at most one invocation. Do not pull/build, use network, or retry during the formal run.
