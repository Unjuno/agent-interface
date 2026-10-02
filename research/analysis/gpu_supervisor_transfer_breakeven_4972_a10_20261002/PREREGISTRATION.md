# Allocation-10 preregistration

## H — hypothesis
For the same confidence-only CONTINUE/YIELD hint with a CPU-owned final admission gate, transfer-inclusive CUDA may have at least 20% lower median per-row latency than CPU at one or more preregistered batch sizes. The GPU path includes Python host-list extraction, host tensor construction, H2D copies, synchronization, D2H copies and the CPU final gate. If no batch clears the threshold, CPU remains preferred for this synthetic workload.

## T — protocol
- Owner question: Issue #5882; successor to the unchanged allocation-08 STOP recorded in #6322 and merged PR #6346. The predecessor had zero candidates, CUDA calls, fits, auditors and retries; it is not a scientific result.
- New allocation/seed: `GPU-SUPERVISOR-TRANSFER-BREAK-EVEN-4972-20261002-10`, seed `49720261010`; branch/path are in FREEZE.json.
- Freeze 1,024 deterministic typed synthetic rows, 256 in each stratum: fresh_valid, stale, ambiguous, forced_yield. The confidence hint threshold is 700 milli-units. Run batch sizes 1, 4, 16, 64, 256 and 1,024; five warmups for each route/size, then 30 alternating paired repetitions.
- Run exactly one candidate in the cached linux/amd64 CUDA image through WSLc, `--pull=never --network none --cpus 2 --memory 2g --gpus all`. Candidate output is a fresh write-only output directory; source is a read-only bind mount. No image pull/build, training, provider/model, GUI, OS input, seed substitution or retry.
- Only after candidate exit 0 and exactly one raw result, run the independent CPU-only auditor once in the same pinned image with no GPU assignment.
- Preserve exact argv, image manifest/config identity, wslc version, start/end inventory, GPU telemetry, stdout/stderr/exit codes, candidate JSON, independent audit receipt and checksums.
- WSLc exposes no root-filesystem read-only or PID-limit option in its CLI. Record this isolation limit explicitly; do not infer enforcement from configured CPU/memory flags. Record cgroup/swap observations where exposed.

## D — decision rule
The independent CPU auditor independently hashes the mounted runner.py and prepare.py, reconstructs every hint/admission from raw rows, checks all six sizes × 30 pairs, validates alternating order and every positive timing, recomputes medians and rejects eight frozen corruption controls (six result mutations plus runner/prepare byte mutations). Any stale, ambiguous or forced_yield row admitted, CPU/CUDA mismatch, missing pair, source/image mismatch or audit error prevents a PASS. If integrity passes and any batch has CUDA p50 per-row end-to-end latency <=80% of CPU p50, disposition is `PASS_TRANSFER_INCLUSIVE_GPU_CROSSOVER_SCOPED`; otherwise it is `PASS_CPU_PREFERRED_NO_GPU_CROSSOVER_SCOPED`. Contract mismatch is FAIL; audit/provenance defect is HOLD; any failed start gate is a terminal pre-candidate STOP. No broad speed or product claim.

## C — caveats
One RTX 3080 Laptop GPU, one machine, one seed and synthetic decisions. Thermal/runtime contention can influence time. WSLc limits may be advisory or partly unenforced. The CPU oracle and CUDA hint operate over tiny integer/boolean vectors; batch sizes do not model a natural supervisor traffic distribution.

## U — unsupported claims
No learned-model quality, training, saved model calls, production authority, real task benefit, natural workload crossover, cross-device/general speedup, or end-to-end Agent Interface efficiency claim.
