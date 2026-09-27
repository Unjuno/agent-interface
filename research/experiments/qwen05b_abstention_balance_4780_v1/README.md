# Issue #4988 — balanced safety-class support for compact local LoRA

Successor to #4792/#4780. Frozen question: does redistributing the same 32 support examples from predecessor-shaped class counts (16/4/4/1/1/1/1/4) to 4 examples in each of eight semantic classes improve held-out action exactness and abstention safety under an identical local LoRA schedule? This directory is additive; predecessor data, source, adapters, and reports remain untouched.

Allocation: `qwen05b-abstention-balance-4780-20260928-01`; formal seed 73194019; construction seed 73194011. Use only the cached Qwen2.5-0.5B-Instruct snapshot and fixed local image identified in Issue #4988. No external training workflow or model download is in scope.

**Execution status: HOLD_GPU_OWNER #4983.** The issue's shared RTX 3080 allocation has priority. No seed/model load, fitting, GPU construction inference, or formal container may start until that allocation's owner explicitly reports release and a fresh GitHub+local collision check clears. The zero VRAM/utilization sample alone is not a release.

No results have been generated for this allocation. Construction/preformal artifact hashes, tests, data inputs, and one-shot formal command must be frozen and read back before any formal execution. Preserve any STOP/FAIL exactly; no retries or retuning.
