# Frozen preregistration — Issue #3701 multi-skill LoRA pilot

Status: source fixed; deterministic CUDA preflight passed; formal allocation not yet started.

## H / T / D / C / U

**H — hypothesis.** Separate, explicitly keyed rank-2 adapters B and C can preserve immutable base skill A and reach at least 0.90 held-out accuracy on each of A/B/C. A single adapter updated sequentially on B then C will exhibit cross-skill interference. Snapshot round-trip and rollback must be verified tensor-by-tensor, not inferred from accuracy.

**T — target and frozen procedure.**
- Allocation: `needle-lora-3441-pilot-04-multiskill`; seed 3443.
- Source: `runner.py`, SHA-256 `4081a3d1e7f353440a2bd6ab45f7d030f6dcfba0f52cfb904c99e79a2fb1cb1e` (9,708 bytes); stored at this branch before formal execution.
- Base: MLP 8→16 tanh→4, trained on 512 rows for 120 full-batch-sampled AdamW updates, LR 0.04, batch 32, seed 3453.
- Synthetic labels: A uses signs of features 0 and 1; B flips feature 0; C flips feature 1. Support rows: 16 each. Held-out rows: 4,096 each. Data seeds 3444–3449, independent and hashed in output.
- LoRA rank 2 on output head; shared control receives 120 updates on B then 120 on C. Separate B/C adapters each receive 120 updates. Fixed initialization seeds 3454–3456; minibatch seeds 3463–3466. AdamW, LR 0.04. No post-evaluation tuning.
- Determinism: Python/PyTorch seeds fixed; deterministic algorithms enabled; CUBLAS_WORKSPACE_CONFIG=:4096:8; cuDNN deterministic and benchmark disabled.
- Device must be NVIDIA GeForce RTX 3080 Laptop GPU, PyTorch 2.5.1+cu121 / CUDA 12.1. Exactly one formal runner invocation; no retry.

**D — measurements/gates.** Record per-skill routed and shared-control accuracies; pretrain and each adapter update time; dispatcher-only overhead; trainable-state snapshot byte lengths and SHA-256; exact tensor equality after snapshot serialization/load and after rollback; invalid-route decisions; base immutability; CUDA peak allocated bytes.
- PASS_MULTI_SKILL_ROUTING_SCOPED only if routed A/B/C each >=0.90, all six invalid routes YIELD, base remains tensor-identical, every snapshot round-trips tensor-exactly, and every rollback exactly restores its pre-update tensors.
- Otherwise classify FAIL_MULTI_SKILL_INTERFERENCE (routed accuracy gate) or FAIL_SNAPSHOT_OR_ROUTE_INTEGRITY (integrity/safety gate). Preserve all measurements even on failure.

**C — constraints and execution.** Synthetic in-memory data only; no provider, network access by the experiment, GUI, input, task submission, policy authority, or runtime integration. Docker Desktop engine pipe was unavailable and service was stopped at preflight; Issue #3701 explicitly authorizes local RTX 3080/CUDA host execution in that case. The formal run is host execution and must not be represented as a container result. No dependencies are installed and no image is pulled. C: had 6.9 MB free; runner is fetched from GitHub into PowerShell memory and executed by Python from an in-memory base64 argument, so no repo or temp artifact is written locally.

**U — limits.** One synthetic seed and related mappings; no realistic skill graph, concurrent updates, crash durability, runtime integration, or action-safety claim. Dispatcher-only timing excludes inference and model load. CUDA peak allocation is not total WDDM/physical GPU memory.

## Coordination and provenance
The exact Issue-prescribed branch name already existed at main with no experiment files; it is untouched. This allocation uses fresh branch `research/needle-lora-3441-pilot-04-multiskill-junny-20260921` from main `e164c32d4c51d19b2d4ba41f0bbb18b64264aa0d`; additive path `research/needle_lora_3441_pilot_04_multiskill/`. Runner commit: `66939822fd67065537fa2fe850f952b5c4a42462`.

## Preflight (not a formal allocation)
2026-09-21 local deterministic CUDA matrix/backprop preflight: PASS; device/version and CUBLAS setting matched frozen requirements. This was environment validation only; no pilot dataset or adapter training was run.
