# Local RTX 3080 GPU research candidate triage — 2026-09-28

The user requested this PC's local resources, no hosted workflow, and emphasis on GPU training/fine-tuning only where justified by a concrete research question.

## Repository direction reviewed

Current main at review: `edbb9c56b6d417705eb37bc5d03facd16743f628`. README holds the rich model fixed and favors bounded local deterministic refinement; learned supervisors are for demonstrated residuals only. CURRENT_GOAL r133 asks for SHA-bound posthoc analysis of DOOM v38/v39 traces, measuring real held-input occupancy, independently useful feedback and bounded recovery, then transferring coverage semantics. ROADMAP still has desktop integration, broad live acceptance and tempo/effect-transfer gaps. GPU training is not inherently required for integration.

The repo's operating method is Issue-first: explicit H/T/D/C/U, exact frozen inputs and decision gates, smallest feasible local container rung, immutable STOP/FAIL/HOLD evidence, independent audit, and reviewable PR. No retry of a consumed allocation.

## Ranked local GPU candidates

### 1. Issue #5014 — Qwen2.5-0.5B balanced-support LoRA

- **H:** the corrected runner executes the fresh paired support-balancing study and passes independent semantic-exactness/safety gates. Predecessor #4988 stopped before model load; it produced no quality result.
- **T:** allocation `qwen05b-abstention-balance-4780-20260928-02`, formal seed 73194109; compare frozen imbalanced 32-example support to balanced 4/class, eight held-out cases in each of eight classes; keep model, initialization, optimizer, budget and other declared controls fixed. Current #5014 and owner branch remain authoritative.
- **D:** use exact #5014 gates: balanced >=80% exact intent/effect, >=15 percentage points over both imbalanced and base, 8/8 each class, no forbidden/stale/unauthorized simulated effects, both fits <=300s, CUDA <=12 GiB, balanced p95 <=1.2s, independent reconstruction, and 5/5 corruption controls. First STOP/HOLD/FAIL is terminal; no retry/tuning/seed swap.
- **C:** local pinned offline container; only selected support-row distribution changes.
- **U:** synthetic study, one cached 0.5B snapshot, one RTX 3080. No live GUI, deployed adapter, cross-device/model or product claim.
- **Status:** CPU construction 8/8 and CPU preflight `PREFLIGHT_OK`, fit count 0. Latest #5014 comment is `HOLD_RESOURCE_OWNERSHIP`: Ollama requests all GPUs and #4917/#4719/#4871 ownership is unresolved. No formal fit. Do not take over without explicit slot transfer.

### 2. Issue #4561 — synthetic visual template-diversity grounding

- **H:** with fixed tiny-CNN initialization/update budget, training on 8 template families instead of 2 improves exact held-out field/submit coordinates.
- **T/D/C/U:** current #4561 frozen three-seed, two-arm, 400-update design and strict validator/auditor; only training-family count changes. CPU renderer PASS is not a CUDA result.
- Existing formal allocation has an owner; no duplicate or rerun. Revisit only after owner confirms terminal/release and handoff.

### 3. Issue #4809 — resident Mitra CUDA inference (not fine-tuning)

- **H:** one resident CUDA trainer meets the frozen six-class probability ABI and warm-p95 gate for sequential/repeated queries.
- Follow frozen one-shot #4809 with pinned local model, fixtures and image, offline inference, zero optimizer updates, exact latency/ABI gates.
- Separate owner and exclusive slot; take only by explicit handoff and never concurrently with #5014.

### 4. Issue #4871 — selected-logit precision boundary

- **H:** BF16/FP32 may restore selected-code logit agreement and retain winner/cache isolation.
- Construction-only comparison on exact frozen corpus/model/IDs.
- Existing v3 is `STOP_CORPUS_HASH_MISMATCH` before model load. Preserve it; any retry requires a fresh successor and verified authoritative corpus.

## Restart gate for #5014

1. Obtain explicit GPU/Docker lease release or transfer; leave caller-owned Ollama/Xvfb containers untouched.
2. Recheck current main, issue/branch/PR/path/output collisions and active local lanes.
3. Read back current freeze/source/data/model hashes; verify construction/preflight receipts and absent formal output.
4. Immediately before the single frozen invocation, re-inventory RTX and Docker ownership.
5. Any failed gate remains STOP/HOLD with zero fit; no retry or freeze edits.
6. Put experiment evidence on #5014's own additive path and PR. This triage is not itself scientific evidence.

No model load, fit, prediction, package installation/download, or container mutation was performed for this triage.
