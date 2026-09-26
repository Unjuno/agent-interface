# Issue #4471 frozen local GPU allocation

## H/T/D/C/U
**H** — After correcting the #3895 base-pretraining count from 120 to the specified 400, fresh-seed explicit per-skill rank-2 LoRA will retain A/B/C held-out accuracy >=0.90 and demonstrate the predeclared advantage over a single adapter trained sequentially B→C, with exact immutable-base/snapshot/rollback and independent-audit evidence.

**T** — Allocation `needle-lora-3441-pilot-04d-corrected-base-20260926-01`; seed 3927; branch `research/needle-lora-3441-pilot-04d-20260926`; additive path `research/needle_lora_3441_pilot_04d_corrected_base_v1/`. Base commit `c83ddb057c680a126144d000bf7ef7ba2274652a`. Preserve #3701/#3895 synthetic 8-feature / hidden-16 tanh / 4-class architecture, rank-2 output adapter, data sizes and seed offsets, AdamW LR .04, batch 32, 16 support rows per skill, 4,096 held-out rows per skill, parameter initialization/training order, dispatch semantics, route controls, full-state snapshot/rollback, row audit and measurements. Only use a new seed and split the previously conflated step parameter into 400 base-pretraining updates and 120 updates per adapter fit. Runner, auditor, construction/corruption tests, expected-data hashes and gates are frozen before any formal optimizer update.

**D** — PASS only with routed A/B/C each >=.90, at least one shared B/C <.90, all invalid routes YIELD, immutable base, exact full-module snapshot/rollback and zero-error row-level CPU audit. If routed accuracy passes but both shared B/C >=.90: HOLD_NO_ROUTING_ADVANTAGE. Routed accuracy miss: FAIL_MULTI_SKILL_INTERFERENCE. Integrity miss: typed FAIL. Environment/provenance failure: STOP/HOLD. One formal invocation, no retry or tuning.

**C** — Local Windows RTX 3080 Laptop GPU, Python 3.11.9, PyTorch 2.5.1+cu121/CUDA 12.1; deterministic CUDA, TF32 off, `CUBLAS_WORKSPACE_CONFIG=:4096:8` before startup. Local host only, not container evidence. Require >=1GiB free C: and >=2GiB free VRAM before formal run. No cloud/HF Jobs, downloads, installs, Docker pull/repair/prune, network/provider, GUI/input, runtime authority or persistent checkpoint. Synthetic in-memory data only.

**U** — One new seed/task family only; no realistic skill-transfer, concurrent/crash-safe persistence, vision/GUI utility, model-load/inference latency, action safety or runtime promotion. #3895's prior HOLD and artifacts remain unchanged.

## Source freeze
Base Git commit: `c83ddb057c680a126144d000bf7ef7ba2274652a`. Files are canonical UTF-8/LF. The following source hashes and Git blob identities were frozen before training:

| File | SHA-256 | Git blob |
|---|---|---|
| `runner.py` | `488bb46b0d38983f340f5815b2b0a9fc00e6dddc102f34639ba08d49de24df97` | `87fcad49af14cf8ac4b57ba9702715f87da45cca` |
| `audit.py` | `972ec02bc549ce7ee5d5bb4f4c0c4a8661ca98567237340e361b356fa9628b2e` | `d1a06776d3e98b21708306d3794f851f0958be5f` |
| `test_construction.py` | `6519277652f51213a73b479531636c2fdd57b24da661bc93539a0810427d7b75` | `43705f499953e2e5a8ca0c686cf62d9eee4ab7ca` |
| `test_audit.py` | `681810d71182fe8e3c9e4ab0fe68a6eeed531fb1605b5c588d203564fc5091ee` | `a17a03d7d9993c5b7d026d053f28bc5afdabfd58` |

The exact hashes for this preregistration are retained in `FREEZE.json`; the freeze file pins all five source files and Git blob IDs above plus this preregistration.
