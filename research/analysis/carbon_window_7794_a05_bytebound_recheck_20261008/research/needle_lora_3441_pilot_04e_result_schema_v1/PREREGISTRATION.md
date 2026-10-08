# Issue #4492 frozen local GPU allocation

## H / T / D / C / U

**H** — With the #4471 result-schema NameError fixed and a fresh non-overlapping seed, the frozen multi-skill LoRA procedure will emit a complete JSON result that the independent CPU auditor can recompute. This can provide a scoped routed-vs-shared outcome; it cannot recover #4471's missing metrics.

**T** — Allocation `needle-lora-3441-pilot-04e-result-schema-20260926-01`; seed 5920; base commit `260c3f088f756eb33d0296298b81fa8d4eafafda`; branch `research/needle-lora-3441-pilot-04e-20260926`; additive path `research/needle_lora_3441_pilot_04e_result_schema_v1/`. Derived dataset seeds 5921–5926 and optimizer/init seeds 5930–5943 were collision-checked. Preserve the #3701/#3895/#4471 synthetic task and all model/data/optimizer settings: 8 input features, hidden 16 tanh core, four classes, rank-2 output adapter; base 512 rows / 400 updates; B/C support 16 rows each; 4,096 heldout rows per skill; adapter 120 steps per fit; AdamW LR .04, batch 32; deterministic CUDA; same init/train order, dispatcher, route controls, full-state snapshot/rollback, independent row audit, and gates.

Only treatment change is the fresh seed. The instrumentation/schema-only correction is to replace #4471's undefined `steps_per_update: STEPS` result field with a pure `parameter_record()` helper exposing explicit `base_pretrain_steps=400` and `adapter_steps_per_fit=120`. A construction-only regression test calls the helper, verifies exact keys/values/JSON serialization, and asserts the AST has no unresolved `STEPS` name. It performs no optimizer update or formal evaluation. Freeze all runner/auditor/test/prereg source identities before formal execution.

**D** — PASS only if routed A/B/C accuracy each >=0.90, at least one shared B/C accuracy <0.90, invalid routes all YIELD, base immutable, full module snapshot/rollback tensor-exact, and independent row-level CPU audit has zero errors. HOLD_NO_ROUTING_ADVANTAGE if routed gates pass but shared B/C both >=0.90. FAIL_MULTI_SKILL_INTERFERENCE for an audited routed quality miss. Typed integrity FAIL or environment/provenance/serialization STOP otherwise. One formal invocation; no retry, tuning, seed substitution, or post-result reconstruction.

**C** — Local Windows RTX 3080 Laptop GPU only; Python 3.11.9 / PyTorch 2.5.1+cu121 / CUDA 12.1; deterministic algorithms, TF32 off, `CUBLAS_WORKSPACE_CONFIG=:4096:8` before process start. Host CUDA is not container evidence. Require >=1GiB free C: and >=2GiB free GPU memory immediately before launch. Peak allocated memory is typed `UNAVAILABLE_WDDM`; do not call the known failing WDDM APIs. No cloud/HF Jobs, network/provider, image pulls, dependency installs, Docker repairs, GUI/input, persistent checkpoints, or runtime authority.

**U** — One fresh seed in one synthetic task family. No realistic skill transfer, concurrent/crash-safe persistence, inference latency, GUI utility, action safety, or runtime-promotion claim. Preserve #4471's STOP and #3895's earlier HOLD exactly; no missing metric may be inferred from them.

## Source identity
Canonical UTF-8/LF SHA-256 and Git blob pins for the four executable/test files are in `FREEZE.json`; this preregistration's own SHA/blob are pinned there as well.
