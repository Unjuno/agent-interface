# Issue #3895 frozen allocation

Status: construction complete; formal GPU run not yet started.

## H / T / D / C / U

**H** — A fresh seed 3444 replication with complete dispatcher-bound predictions and full-module snapshot checks can evaluate the synthetic multi-skill routing behavior without the protocol gaps that forced #3701 to HOLD.

**T** — One seed (3444), exact #3701 8-feature / hidden-16 / four-class synthetic task, base pretraining (512 rows, 120 steps), rank-2 output LoRA, 16 B and 16 C support rows, 120 updates per arm, batch 32, AdamW LR .04. Data/task/optimizer seed offsets and update order are pinned in FREEZE.json. Compare base A and separately routed B/C adapters to the single shared adapter sequentially updated B then C. Only seed changes from #3701's supplemental 3443; instrumentation adds dispatch-returned-model scoring, complete row predictions/labels, full module state_dict snapshots/rollback including frozen core, and isolated synchronized adapter setup time. No tuning.

**D** — PASS only if dispatched A/B/C accuracy >=.90, invalid routes YIELD, base is unchanged, complete module state round-trip/rollback is exact, and the independent CPU auditor regenerates expected labels/recomputes every row-level metric with zero errors. Quality miss is FAIL_MULTI_SKILL_INTERFERENCE; state/route/audit integrity miss is typed FAIL; setup/provenance/environment ambiguity is STOP/HOLD. One invocation, no retries.

**C** — Local Windows RTX 3080 Laptop GPU, Python 3.11.9, PyTorch 2.5.1+cu121, CUDA 12.1; deterministic algorithms on, TF32 off, CUBLAS_WORKSPACE_CONFIG=:4096:8 set before process startup. Docker unavailable, so no container claim. Minimum 1GiB system disk and 2GiB free VRAM. No dependency installation, pull, network, provider, GUI/input, runtime authority or persistent checkpoint.

**U** — One fresh seed in one synthetic task family. No realistic skill transfer, concurrency, crash durability, inference latency, GUI usefulness, runtime integration or action safety claim. Earlier HOLD/STOP remain immutable.

## Provenance and preallocation checks

Branch `research/needle-lora-3441-pilot-04c-20260921` was created from current main head `cc9c500a339406c7de71df04c1d4b23f12fdbb09` after exact-name collision checks. The inherited reference runner is the exact #3701 retained file (Git blob `b5689ddeaf88715217ad69b4ce46d56ec75a7491`, SHA-256 `4081a3d1e7f353440a2bd6ab45f7d030f6dcfba0f52cfb904c99e79a2fb1cb1e`). Updated source and construction suite hashes are pinned in FREEZE.json.

Construction suite: 8/8 passed; no optimizer step or formal training/evaluation occurred. Current preflight: RTX 3080 Laptop GPU, 16177 MiB free VRAM; C: 434750402560 bytes free; Python 3.11 CUDA stack satisfies frozen versions. Other concurrent open PRs were enumerated; no matching branch/path or same-seed active owner found.

