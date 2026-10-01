# Transfer-inclusive CPU/CUDA break-even probe (successor to #4972)

This allocation is an independent follow-up to #4972/#5813. Their resident-input timings and results are immutable and are not pooled here.

## H / T / D / C / U

**H.** Transfer-inclusive CUDA will be slower for small batches and may cross a break-even point at a larger preregistered batch size. If no tested size crosses the threshold, retain CPU as preferred for this workload.

**T.** One fresh 1,024-row synthetic typed dataset, 256 rows per stratum (`fresh_valid`, `stale`, `ambiguous`, `forced_yield`), seed `49720261003`; sizes 1, 4, 16, 64, 256, 1,024; 5 warmups and 30 alternating paired CPU/CUDA timings per size. Each CUDA end-to-end sample includes extracting host lists, constructing tensors, H2D, hint compute, synchronization, D2H, and the CPU final gate. Retain every timing sample and raw decision pair. One candidate; only exit 0 permits one independent CPU-only raw audit. No fitting/training, model/provider, network, GUI, input, retries, or tuning substitutions.

**D.** Exact CPU/CUDA hint and final-gate parity for all rows in each tested batch; zero admissions for stale, ambiguous, or forced-YIELD rows; 1,024-row stratum counts and all raw timing samples reconstruct; five frozen corruption controls reject. If integrity passes and median end-to-end CUDA latency per row is at least 20% below CPU at any tested size, report `PASS_TRANSFER_INCLUSIVE_GPU_CROSSOVER_SCOPED` with first crossing size. If audit/parity pass but no tested size crosses, report `PASS_CPU_PREFERRED_NO_GPU_CROSSOVER_SCOPED`. Parity failure: `FAIL_CPU_CUDA_CONTRACT`; provenance/audit defect: `HOLD_INTEGRITY`; setup/resource failure: `STOP`. No cross-device or broad speed claim.

**C.** This Windows host, its local RTX 3080 Laptop GPU, exact locally present frozen Windows host runtime (Python 3.11.9, PyTorch 2.5.1+cu121, CUDA 12.1, NVIDIA GeForce RTX 3080 Laptop GPU), synthetic rows, and observed thermal/load conditions only. CPU remains the final authority; CUDA output is a non-authoritative hint.

**U.** No natural batch-size distribution, live route prevalence, model-call savings, task success, GUI/game behavior, production efficacy, or cross-host generalization. Batch-size sweep is synthetic unless independently frozen current-main trace data is established before result inspection.

## Invocation boundary

Candidate: `python runner.py`, once. Separate auditor: `python audit.py`, once only after candidate exit 0. The result path is unique to this allocation. At launch, recheck exact current main, queue handoff/lease, local pinned image digest/platform and source/data hashes, empty outputs and adequate stable disk space, GPU/process/container inventory, and no path/ref collision. Any failed gate is a pre-candidate STOP; never retry this allocation.

