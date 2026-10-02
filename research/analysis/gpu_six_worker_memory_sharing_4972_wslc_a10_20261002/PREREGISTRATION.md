# WSLc-native six-worker GPU memory-coexistence probe

This is a fresh runtime allocation under existing Issue #6329. The prior #6329 allocation-09 Podman/crun STOP remains immutable and is not retried. No separate resource-only Issue is created.

## H / T / D / C / U

**H.** On this host's 16-GiB RTX 3080 Laptop GPU, six independent processes can concurrently hold a fixed 192-MiB CUDA working set, rendezvous with every allocation live, and complete deterministic integer arithmetic while keeping global free VRAM at or above 4 GiB. This tests bounded memory coexistence only, not CUDA speedup.

**T.** Allocation `GPU-MEMORY-SHARING-4972-20261002-10`; fresh seed `49720261010`; branch `research/gpu-six-worker-memory-sharing-4972-wslc-a10-20261002`; additive path `research/analysis/gpu_six_worker_memory_sharing_4972_wslc_a10_20261002/`; base main SHA is recorded in `FREEZE.json`. Six spawned CUDA workers each set a 5% PyTorch allocator cap, allocate one 24*1024*1024 int64 tensor (exactly 192 MiB), synchronize at a six-way barrier, perform 20 in-place increments, and emit PID/device/seed/allocation/checksum/free-memory evidence. A separate Windows-host `nvidia-smi` sampler records global GPU telemetry once per second during the candidate. Candidate maximum 1; a separate raw-only CPU auditor maximum 1 only after candidate exit 0; retries 0.

Run only through Microsoft's WSL Containers `wslc.exe`, with the cached exact `pytorch/pytorch@sha256:831247999fbf7e08f61b3e39f6d77ee434f38f6f07f769d00db451e853878067` linux/amd64 image, `--pull never`, `--network none`, `--gpus all`, `--cpus 6`, `--memory 8G`, and UID/GID 65534:65534. The source and host telemetry are read-only binds; only a fresh candidate output directory is writable. Audit is a separate network-disabled WSLc container without GPU access. No Podman, Docker Desktop, image pull/build, model/provider, GUI, user input, or task dispatch.

The WSLc CLI does not expose a read-only rootfs or PID-limit option. The container root layer remains ephemeral but writable; the 6-process candidate is bounded by the script, 110-second worker deadline, CPU and memory settings, unprivileged UID, no network, and narrow mounts. WSLc has reported cgroup/swap-limit caveats; no hard memory+swap isolation claim is made. Record the exact warning from the formal invocation.

**D.** `PASS_SHARED_MEMORY_COEXISTENCE_SCOPED` only if worker IDs 0..5 occur exactly once, PIDs are unique, all use the RTX 3080 and allocate exactly 192 MiB, all rendezvous, return success, complete 20 increments, match independent CPU checksum reconstruction, each allocator peak remains at or below 5% of device capacity, synchronized worker global-free samples and every host-sampler row remain at or above 4 GiB, the host baseline is at or above 10 GiB, aggregate worker allocator peak is at or below 8 GiB, all six child exit codes are zero, and all four frozen mutation controls are rejected. Missing/malformed/duplicate records, OOM, device loss, checksum/audit mismatch, or threshold breach cannot be PASS. No timing criterion.

**C.** One laptop and fixed synthetic arithmetic. CUDA contexts, WSLc/driver behavior, allocator accounting and unrelated GPU tenants affect global use. Per-process allocator fractions do not constrain CUDA-context allocation; independent global free-memory telemetry and the 4-GiB reserve are required.

**U.** Does not establish safe memory for arbitrary models, six complete agent workloads, unbounded co-tenants, training, production readiness, or performance benefit. WSLc still uses this same host GPU.

## Start and stop gates

Require one exact coordinator-assigned exclusive host-GPU interval recorded on Issue #5085; current main equal to `FREEZE.json`; matching source/image hashes and linux/amd64 image identity already cached; known container/process ownership; no output path; host C: free space at least 1 GiB; RTX 3080 identity and at least 10 GiB free VRAM; no unresolved competing owner. Any failed gate means typed STOP before candidate launch and zero CUDA calls. Never stop or modify another task's process/container/distro. Any unassigned interval remains deferred; elapsed time or idle `nvidia-smi` is not a grant.

The shared-RTX queue currently has a separate #6354 request pending. This package does not claim an interval or start permission. Arbitrate only after that request has an explicit terminal/release disposition; do not create another reservation thread or resource-only Issue.
