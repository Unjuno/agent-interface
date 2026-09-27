# Issue #59 — RTX 3080 HUD ROI replay

This additive diagnostic replays the 13 hash-pinned decision frames from the retained failed Astra MAP01 run through the existing one-way health-ROI change metric. The frozen 95x50 ROI is [440,585,535,635], RGB max-channel threshold >32, and invalidates at >=100 changed pixels.

The first preregistration (`PREREGISTRATION.json`) stopped before comparison because it incorrectly expected 640x560 frames; actual input is 1280x800. That STOP is retained. The separate `PREREGISTRATION_V2.json` records the correct geometry before its bounded replay. A pre-comparison attempt using `torch.cuda.reset_peak_memory_stats` then stopped with `RuntimeError: Invalid device argument`; the working set was changed to observe before/after allocation only, without resetting CUDA statistics, and a single replay completed.

Result: `PASS_GPU_CPU_EXACT_PARITY`. The 12 consecutive pairs had exact CPU/CUDA changed-pixel counts and identical statuses: 7 INVALIDATED and 5 UNCHANGED. An independent script reconciled every pair against the retained manual label counts. CUDA was PyTorch 2.5.1+cu121 on NVIDIA GeForce RTX 3080 Laptop GPU. Single diagnostic timing including transfer/compute: 140.148 ms; allocation 0 -> 186,368 bytes. These descriptive numbers do not establish speedup.

Scope: post-hoc, postselected frames from one failed run. No Doom process, model inference, Docker, or input control was used. The comparison establishes implementation parity only. The signal may only revoke an existing policy and request a new decision; it does not identify a threat, grant authority, prove success, prevent damage, or validate live sampling. GPU adoption for this tiny ROI remains unproven.
A separate v2 pre-comparison STOP records the unsupported CUDA peak-memory reset call; after read-only confirmation that basic tensor execution works, the one allowed correction observed before/after allocation without resetting counters.

A separate v2 pre-comparison STOP records the unsupported CUDA peak-memory reset call; after read-only confirmation that basic tensor execution works, the one allowed correction observed before/after allocation without resetting counters.
