# Allocation-06 preregistration

Issue #5882; fresh successor after allocation-05 expired before candidate. Prior allocations and outcomes remain immutable.

## H / T / D / C / U

**H.** For a confidence-only CONTINUE/YIELD hint with a CPU-owned final gate, transfer-inclusive CUDA is slower for small batches but could be at least 20% faster per row at a larger preregistered batch size. If no size clears the threshold, CPU remains preferred for this synthetic workload.

**T.** Allocation GPU-SUPERVISOR-TRANSFER-BREAK-EVEN-4972-20261002-06; seed 49720261006; 1,024 fresh synthetic typed rows with 256 each in fresh_valid, stale, ambiguous, forced_yield; batch sizes 1, 4, 16, 64, 256, 1,024; five warmups and 30 alternating paired repetitions per size. Runtime is one RTX 3080 Laptop GPU passed through Docker Desktop desktop-linux to cached linux/amd64 image pytorch/pytorch@sha256:831247999fbf7e08f61b3e39f6d77ee434f38f6f07f769d00db451e853878067. Exact owner-bound interval: 2026-10-01 22:45:00Z to 23:00:00Z. Run one candidate container; only if it exits 0, run one separate CPU-only raw auditor container. Retries=0. No network, image pull/build, model/provider, GUI/game/input, training, or substitution.

**D.** Exact per-row CPU/CUDA hint and admission parity at each sampled prefix; stale, ambiguous, and forced-yield rows never admitted; exact 1,024 row/stratum accounting and 30 timing pairs for each size; timing medians reconstruct; the independent raw-only auditor reports zero errors and rejects all six controls (flipped CUDA hint, missing timing sample, wrong source hash, duplicate pair, unsafe admission, wrong image ref). If integrity passes and CUDA median end-to-end latency per row is at least 20% lower than CPU at any preregistered size, report PASS_TRANSFER_INCLUSIVE_GPU_CROSSOVER_SCOPED and the first qualifying size. If integrity passes and no size qualifies, report PASS_CPU_PREFERRED_NO_GPU_CROSSOVER_SCOPED. Contract mismatch => FAIL_CPU_CUDA_CONTRACT; raw/provenance defect => HOLD_INTEGRITY; runtime, ownership, or capacity gate => STOP_BEFORE_CANDIDATE.

**C.** One Windows host, Docker Desktop Linux/amd64, one exact cached image digest, one RTX 3080 Laptop, synthetic data, host load/thermal conditions. CUDA emits only a non-authoritative hint; the final gate remains CPU-owned.

**U.** Does not establish natural batch-size prevalence, end-user/task benefit, model-call savings, GUI/game behavior, production efficacy, or cross-device speed.

## Start gate and execution

Immediately before the slot, re-read main and #5085 queue; confirm this exact owner-bound slot is unconflicted; verify the exact image RepoDigest and platform, source/data/freeze hashes, absent output, no running container in this Docker context, idle RTX 3080, at least 1 GiB free on C: with two nondecreasing readings at least 60 seconds apart. Use --pull=never --network none, a read-only root/source mount, bounded CPU/memory/PIDs, and separate writable output mount. Candidate and audit each have at most one invocation. Any failed or ambiguous pre-candidate gate is terminal STOP and immediate release. A candidate nonzero exit forbids audit and retry. Preserve all raw bytes and outcomes.
