# Allocation 12 preregistration

## H — hypothesis
For the synthetic confidence-only CONTINUE/YIELD hint with CPU-owned final admission, transfer-inclusive CUDA can reduce median per-row latency by at least 20% for at least one preregistered batch size. Otherwise CPU remains preferred for this tested synthetic workload.

## T — treatment
Fresh allocation `GPU-SUPERVISOR-TRANSFER-BREAK-EVEN-4972-20261002-12`, seed `49720261012`, current-main freeze recorded in FREEZE.json. Use 1,024 deterministic typed synthetic rows (256 each: fresh_valid, stale, ambiguous, forced_yield); batch sizes 1, 4, 16, 64, 256, 1,024; five warmups and 30 alternating paired repetitions. One candidate run in Microsoft WSLc with the pinned linux/amd64 PyTorch CUDA image and RTX 3080 Laptop GPU. Include host-list extraction, tensor construction, host-to-device transfer, CUDA compute, synchronization, device-to-host transfer, and CPU final-gate evaluation. Run one separate CPU-only raw auditor only if the candidate exits 0 and emits exactly one result. Retry=0.

## D — decision
Require exact CPU/CUDA hint and admission parity on every recorded pair; zero admissions for stale, ambiguous, and forced-yield rows; complete reconstruction of all dataset strata, six batch sizes, 30 pairs and timings; frozen source/data/image identities; and rejection of every frozen corruption control. If all integrity/contract conditions pass and any CUDA median end-to-end per-row latency is <=80% of CPU, report `PASS_TRANSFER_INCLUSIVE_GPU_CROSSOVER_SCOPED` and the first qualifying batch size. Otherwise report `PASS_CPU_PREFERRED_NO_GPU_CROSSOVER_SCOPED`. Contract mismatch is FAIL; audit/provenance defect is HOLD; failed owner/runtime/main/image/output gate is terminal pre-candidate STOP.

## C — context
One physical Windows host, one RTX 3080 Laptop GPU, Arch Linux WSL2, WSLc 3.0.1.0, one pinned PyTorch CUDA image, synthetic rows, and current thermal/background state. WSLc resource flags are recorded as requested settings only unless the guest kernel confirms enforcement. The GPU remains a non-authoritative hint; final admission is CPU-owned.

## U — unknowns
One synthetic finite benchmark does not establish a natural batch-size distribution, model-call savings, task quality, GUI/game behavior, safety, production benefit, general GPU speedup, or cross-device reproducibility.

## Start gates
Before candidate: exact assigned non-overlapping GPU interval in #5085; fresh owner/conflict refresh; current main equals the SHA in FREEZE.json; branch and package hashes match; exact image digest and linux/amd64 identity match; output path absent; WSLc reports no running containers; GPU process/use inventory is empty and capacity is stable. Any failed gate => STOP before candidate. Preserve all prior A03–A11 outcomes and do not use any of their seed, data, timing or output.
