# Frozen preregistration — Issue #3442 Intent-Aligned Local System-1

Allocation: `intent-aligned-system1-3442-pilot-01`
Immutable publication base: `f79ef46d478911170d73b71bddcbe58fd698dc84`
Branch: `research/intent-aligned-system1-3442-pilot-01`
Path: `research/system1/intent_alignment_3442_pilot_01/`
No formal training/evaluation allocation has started as of this freeze.

## H — hypothesis

For an identical observed local state whose correct bounded proposal changes with Rich Model intent, a small policy supplied with an explicit, versioned intent identifier will preserve the intent-dependent proposal substantially better than the same fixed-size policy without intent input. A separate deterministic gate will emit `YIELD` on stale intent version, stale evidence version, or unknown intent identity. Model output is never execution authority.

## T — frozen target and procedure

- Comparison: two 6-32-32-4 tanh MLPs with identical initialization, AdamW optimizer, learning rate, weight decay, training examples, minibatch schedule and 500 updates. Baseline receives four state features plus two zero context slots. Conditioned arm receives the same state plus a two-bit one-hot intent context.
- Synthetic intents: `target-left-v1` and `target-right-v1`; same observation states are paired across both intents. Typed output vocabulary: `LEFT`, `RIGHT`, `WATCH`, `YIELD`.
- Data seeds: train 344201 (1,024 unique states, each paired across two intents); held out 344202 (512 unique states, each paired across two intents); minibatch schedule 344204; initialization 344205.
- Inputs are position, velocity, observation age, and scope bit. The deterministic teacher yields on stale/invalid/out-of-envelope state; otherwise it proposes a bounded correction or WATCH.
- Frozen runner SHA-256: `83e59427cebcbffa3c7be76e89f4ffe483727cf4f87dc0efb54539b580724751`.
- Frozen independent audit SHA-256: `174697be81c436fe615fffff61a14f185024ba1306b71d47504faea999b83a53`.
- Run exactly one formal invocation after construction checks. Retain model weights, every held-out row and proposal, latency samples, data hash, environment and complete stdout JSON. No retry or post-result tuning.

## D — decision gates

`PASS_INTENT_CONDITIONING_SYNTHETIC_SCOPED` only if all are true:

1. Conditioned held-out accuracy >=0.95.
2. Absolute gain over the no-intent baseline >=0.20.
3. Both intent-specific predictions are correct on >=0.90 of paired held-out states.
4. All stale-intent, stale-evidence, and unknown-intent controls yield; all matched controls remain authority-neutral `PROPOSE`.
5. Conditioned single-state CPU inference p95 <60 ms.
6. Independent auditor recomputes held-out rows, model outputs from retained weights, data split identity, accuracy/pair rates, latency p95 and gate counts with zero errors.

Any missing integrity evidence is HOLD; numeric gate misses are retained as FAIL/HOLD per the measured failure. No action execution is part of this allocation.

## C — constraints and execution environment

- No GUI, OS input, provider/network request, user data, runtime integration, or policy authority.
- Docker Desktop Linux engine is unavailable (missing `dockerDesktopLinuxEngine` named pipe; `com.docker.service` Stopped/Manual). C: reports 0 free bytes. To avoid any local artifact/cache writes, execute this small, CPU-only synthetic allocation in memory with Python `-B`, `PYTHONDONTWRITEBYTECODE=1`, and explicit CPU tensors; publish files via GitHub API. This is host execution, not container verification.
- Environment preflight: Windows host enumerates Intel Iris Xe and NVIDIA RTX 3080 Laptop GPU; Python 3.11.9, PyTorch 2.5.1+cu121. The formal runner must use CPU and not initialize CUDA.
- Do not free disk, start/restart Docker, install dependencies, pull images, or write local result files.

## U — limits

One synthetic paired-intent task and one training seed. Context is a one-hot intent ID plus version-equality control, not a cryptographic signature or real Rich Model trajectory. This does not establish real GUI alignment, Astra-label transfer, online LoRA/finetuning, multi-role network composition, skill reuse, action safety, or an integrated/runtime benefit. A pass is only evidence that the tested synthetic decision requires an intent input to avoid the constructed ambiguity.

## Construction evidence before formal allocation

The first construction invocation at branch commit `493b8369ec88a074ad0da14d55c8c57aec7f3118` returned 6/7: the vocabulary assertion expected an eight-row random sample to contain every output class. It performed no optimizer update or held-out evaluation. The validation fixture—not the scientific hypothesis—was corrected to four fixed states covering all four labels. Current frozen runner construction checks pass 7/7; the independent audit self-test passes 4/4. Full history: [CONSTRUCTION.md](CONSTRUCTION.md).

