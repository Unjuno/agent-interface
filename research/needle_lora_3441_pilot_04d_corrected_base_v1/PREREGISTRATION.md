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
| `runner.py` | `b9dcf1e9720adef96e095d02e26bd61171c5453ba382880300cca11efaadd357` | `e76e1582f12db745c5c3b1140b1393079265fff7` |
| `audit.py` | `1f663574f605612aafb80a422c805f068b6c4fcfb1ea32bd5f4baeefe69d7c9c` | `7ed931198030a809a105490ab2c4aa0568cc0f3c` |
| `test_construction.py` | `fa01c208e0566b64ab5867345df6c6ec2a58b8a29551d8b090973cf78dd38b0d` | `2231296afd4cfe04bf7b99c3e99b51b6de71e352` |
| `test_audit.py` | `681810d71182fe8e3c9e4ab0fe68a6eeed531fb1605b5c588d203564fc5091ee` | `6bb1aaba4826bfe06ea2a9f40897182875d4d63b` |

The exact hashes for this preregistration are retained in `FREEZE.json`; the freeze file pins all five source files and Git blob IDs above plus this preregistration.


## Pre-formal WDDM instrumentation amendment

Before any training, a read-only GPU-memory instrumentation probe reproduced `torch.cuda.reset_peak_memory_stats(cuda:0)` failing with `RuntimeError: Invalid device argument` on the local Windows WDDM host. No optimizer step, training or evaluation occurred. The unsupported peak-memory calls are removed from the frozen runner; `cuda_peak_allocated_bytes` is recorded as null and `cuda_peak_memory_status` as `UNAVAILABLE_WDDM`. This is instrumentation-only and leaves all treatment variables and outcome gates fixed. The test suite verifies these unsupported calls are absent and the typed measurement state is reported.
