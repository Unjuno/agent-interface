# 04e fresh-seed local CUDA LoRA result

## H / T / D / C / U

**H** — With only the result-schema NameError corrected and a fresh seed, the fixed local CUDA multi-skill LoRA procedure emits a complete JSON result independently auditable at row level, allowing a scoped routed-versus-shared decision. This cannot recover the missing #4471 result.

**T** — Allocation `needle-lora-3441-pilot-04e-result-schema-20260926-01`; seed 5920; additive path `research/needle_lora_3441_pilot_04e_result_schema_v1/`; frozen source branch `research/needle-lora-3441-pilot-04e-20260926`. Windows host RTX 3080 Laptop, Python 3.11.9, PyTorch 2.5.1+cu121, CUDA 12.1. One invocation with `CUBLAS_WORKSPACE_CONFIG=:4096:8` and `PYTHONHASHSEED=5920`; no retry or tuning.

**D** — `PASS_MULTI_SKILL_ROUTING_SCOPED`. The runner exited 0 and emitted 817,026 bytes of JSON; stderr was empty. Independent CPU audit exited 0, recomputed 24,576 prediction rows, and returned zero errors. Routed accuracy: A 0.965332, B 0.941162, C 0.926514 (all >=0.90). Shared sequential accuracy: A 0.078857, B 0.001221, C 0.872070 (B/C include the preregistered routing-advantage control below 0.90). All six invalid routes yielded; shared base remained immutable; full-state snapshot roundtrip and rollback were tensor-exact. Base training used 400 steps; each adapter fit used 120. Peak CUDA allocation is typed `UNAVAILABLE_WDDM`.

**C** — This is one seed in a small synthetic four-class task with three skills. It is not realistic skill transfer, a live agent/runtime result, inference-latency measurement, concurrent/crash-safe persistence, GUI utility, action safety, or runtime promotion. No container evidence is claimed: #4492 specifically requires Windows host CUDA.

**U / lineage** — The result-schema correction has a pure helper regression test. The earlier #3895 120-base-step protocol deviation and #4471 post-training serialization STOP remain unchanged; no outcome is inferred from them. The first preflight note incorrectly treated a container image as mandatory; that interpretation was superseded before formal execution after rereading #4492's explicit “Host CUDA only, not container evidence” condition. Formal invocation count is one.

## Evidence

- Exact formal JSON stdout: `FORMAL_STDOUT.json`, SHA-256 `11717819e6fbac564c57d618e1f3ee8110b4ba0447e067584cb57c790566325e`.
- Empty stderr SHA-256: `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`.
- Independent audit: `AUDIT.json`; full command, environment, timing and identity record: `FORMAL_METADATA.json`.
- Frozen source, preregistration and Git blob pins: `FREEZE.json`.
- Construction/auditor suite: 17/17 PASS before formal invocation.
