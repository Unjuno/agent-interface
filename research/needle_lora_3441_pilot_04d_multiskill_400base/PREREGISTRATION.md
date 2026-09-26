# Issue #3912 frozen allocation

Status: construction candidate; formal GPU run has not started.

## H / T / D / C / U

**H** — With explicit fail-closed routing, separate rank-2 adapters can preserve synthetic A/B/C held-out accuracy >=0.90 while a shared adapter updated B then C exhibits cross-skill interference. This single-seed result is scoped only.

**T** — Allocation `needle-lora-3441-pilot-04d-multiskill-400base`, seed 3914. Exact task family/architecture/optimizer/learning rates/data offsets/update seeds and evidence contract as #3895's corrected runner, except base skill A is trained on 512 rows for **exactly 400 AdamW optimizer updates** (the #3895 frozen runner used 120, so that allocation remains HOLD). B/C supports are 16 rows each; each separate adapter and the sequential shared B-then-C arm receives 120 updates, batch 32, AdamW LR .04, rank 2. Evaluate base A and dispatched B/C on 4096 held-out rows each; preserve each expected label and selected-model prediction. Independently regenerate labels and recompute all six routed/shared row metrics. Require full adapted-module state roundtrip/rollback, base immutability, route YIELD controls, isolated setup/update/dispatch timing. Exact hashes are in FREEZE.json. One formal local GPU invocation only; no tuning, seed substitution, or retry.

**D** — Scoped PASS requires all routed A/B/C >=.90, all invalid routes YIELD, base immutable, full-state snapshot and rollback exact, complete row audit and identity/hash bindings. A valid quality miss is `FAIL_MULTI_SKILL_INTERFERENCE`; tensor failure is `FAIL_SNAPSHOT_INTEGRITY`; route/audit failure is `FAIL_ROUTE_OR_AUDIT_INTEGRITY`. Environment/protocol/provenance gaps are typed STOP/HOLD. Secondary interference support requires mean routed B/C accuracy minus mean shared B/C accuracy >=.10; otherwise report that hypothesis unsupported separately from primary routing outcome.

**C** — Local Windows RTX 3080 Laptop GPU, Python 3.11.9, PyTorch 2.5.1+cu121 / CUDA 12.1; deterministic algorithms, TF32 off, `CUBLAS_WORKSPACE_CONFIG=:4096:8` set before process start; minimum 1 GiB free system disk and 2 GiB free VRAM. Host execution is not a container PASS. No network/provider, GUI/input, action submission, runtime authority, installation, image pull, Docker repair, or destructive cleanup. Preserve a pre-update typed STOP if any prerequisite fails.

**U** — One fresh seed and one related synthetic task family only; no real skill transfer, concurrency, durable persistence, end-to-end inference latency, GUI usefulness, runtime integration, safety, or action-authority claim.

## Provenance and freeze

Branch `research/needle-lora-3441-pilot-04d-20260921` is based on main `8085e682f6363ec4cd95648e55c16dfca9049dd0`. Additive path is `research/needle_lora_3441_pilot_04d_multiskill_400base/`. Runner, auditor and construction test source pins are in FREEZE.json. Construction test outputs will be recorded before the one formal invocation; no optimizer update may occur during construction tests.

The earlier #3895 raw run and HOLD remain unchanged. The #3895 outcome is not pooled with this fresh seed.
