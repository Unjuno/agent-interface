# Allocation-05 transfer-inclusive GPU break-even preregistration

Issue #5882; successor to #4972/#5813. Allocation-03 remains immutable HOLD_INTEGRITY. Allocation-04 was withdrawn before candidate due queue collision; it is not reused.

## H / T / D / C / U

**H.** Transfer-inclusive CUDA hint evaluation is slower for small batches and may cross CPU at a larger tested batch size. If no tested size crosses the threshold, retain CPU as preferred for this workload.

**T.** New allocation GPU-SUPERVISOR-TRANSFER-BREAK-EVEN-4972-20261001-05; base main c427c704404fc2b35ea9e06a57e61d239b77b369; seed 49720261005; 1,024 fresh typed synthetic rows (256 each: fresh_valid, stale, ambiguous, forced_yield); sizes 1, 4, 16, 64, 256, 1,024; five warmups and 30 alternating paired repetitions per size. CUDA end-to-end timing includes host-list extraction, tensor construction, H2D, hint compute, synchronization, D2H, and CPU-owned final admission gate. One Windows-host RTX 3080 Laptop only. The exclusive interval is 11:30–11:40 UTC on 2026-10-01, subject to a fresh exact start gate. Candidate once, independent CPU raw-only auditor once only after candidate exit 0; retries 0. No Docker/WSL, model/provider, network, GUI/game/input, fit/training, or substitutions.

**D.** Require exact row-wise CPU/CUDA hint and admission parity for every sampled prefix; zero admission for stale, ambiguous, and forced-yield rows; exact 1,024-row stratum and timing reconstruction; and rejection of all five frozen corruption controls. If integrity passes and CUDA median end-to-end latency per row is at least 20% lower than CPU at any preregistered size, report PASS_TRANSFER_INCLUSIVE_GPU_CROSSOVER_SCOPED with the first qualifying size. If all integrity gates pass but none qualifies, report PASS_CPU_PREFERRED_NO_GPU_CROSSOVER_SCOPED. Contract mismatch => FAIL_CPU_CUDA_CONTRACT; provenance/raw audit defect => HOLD_INTEGRITY; setup/ownership/resource failure => STOP.

**C.** One Windows host, exact local runtime recorded in FREEZE.json, one RTX 3080 Laptop, synthetic data and observed thermal/load conditions. CUDA produces only a non-authoritative hint; the final gate remains CPU-owned.

**U.** No natural batch-size distribution, production prevalence, model-call savings, task success, live GUI/game behavior, or cross-device/general speed claim.

## Start and stop rules

Immediately before candidate, refresh exact main, #5085 queue and active owners; verify the exact owner-bound window, runtime/device, source/data/freeze hashes, at least 1 GiB free on C: with two readings at least 60 seconds apart showing no decrease, no competing Python/CUDA workload, and absent local/remote output. Any failed or ambiguous gate is a terminal STOP before candidate and immediate slot release. Preserve raw candidate bytes and auditor output without rewriting prior allocations. If main advanced from the frozen SHA, synchronize the additive branch and update only the main-base/time fields; reverify all source/data hashes before candidate.
