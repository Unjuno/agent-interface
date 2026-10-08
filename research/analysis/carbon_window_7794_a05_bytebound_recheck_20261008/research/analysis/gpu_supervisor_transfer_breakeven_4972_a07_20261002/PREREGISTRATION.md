# Allocation-07 preregistration

Issue #6308; successor to #5882 allocation-06's pre-candidate capacity STOP. All predecessors remain immutable.

## H / T / D / C / U

**H.** Once host tensor construction, H2D, CUDA compute/synchronization, D2H and the CPU-owned final gate are included, CUDA may cross a 20% per-row latency advantage only at larger synthetic batches; otherwise CPU remains preferred.

**T.** Allocation GPU-SUPERVISOR-TRANSFER-BREAK-EVEN-4972-20261002-07; fresh seed 49720261007; base main d7e20a0d25e0c361d1e7cf56fd103f61fb927a2d at branch creation. Generate 1,024 deterministic rows (256 each fresh_valid/stale/ambiguous/forced_yield). Benchmark sizes 1,4,16,64,256,1024, with five warmups and 30 alternating paired repetitions. Exact #5882 runner/auditor lineage; no tuning or timing reuse. Cached PyTorch 2.5.1+cu121 CUDA image only, RTX 3080 Laptop, Docker Desktop desktop-linux, no pull/build/network. Candidate one invocation; independent raw audit only after candidate exit 0; retries 0.

The exclusive interval is only requested in #5085: 2026-10-01 23:45–2026-10-02 00:15 UTC, after #6296's 23:10–23:40 owner-bound allocation and explicit release. This request is not a grant. Refreeze/sync if main moves. At start require exact grant, clear owner/queue, stable >=1 GiB disk on two nondecreasing readings >=60 seconds apart, empty containers/output, correct RTX/image/source/data identities. Otherwise STOP before candidate.

**D.** Exact per-row hint/admission parity for CPU and CUDA at each size/repetition; no unsafe admission; 30 paired timing values per route/size and independently recomputed medians; six frozen corruptions rejected. PASS_TRANSFER_INCLUSIVE_GPU_CROSSOVER_SCOPED iff all integrity/audit gates pass and CUDA median per-row end-to-end latency is >=20% lower for any size; else PASS_CPU_PREFERRED_NO_GPU_CROSSOVER_SCOPED if parity/audit pass. Contract discrepancy FAIL; provenance/audit HOLD; gate failure STOP.

**C.** One laptop GPU, one host/runtime and a synthetic input distribution. Thermal/load/transfer conditions limit timing scope. Native WSL Arch lacks PyTorch; WSLc has only cached Python image, while the exact pinned PyTorch CUDA image is cached in Docker Desktop. No image acquisition allowed.

**U.** No natural batch-size distribution, model-call reduction, task success, broad GPU advantage, production authority, or Agent Interface end-to-end benefit.
