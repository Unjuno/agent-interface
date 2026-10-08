# Issue #5014 — preregistered successor to #4988

The predecessor #4988 ended in a runner/schema STOP before model load. It consumed no fit and yielded no model result. This allocation is fresh: all formal input rows and seeds are new; preserve #4988 unchanged.

## H — hypothesis

Under an equal 32-row support budget, balanced exposure across the eight frozen semantic classes can improve held-out exact intent/effect and abstention safety compared with the predecessor-shaped 16/4/4/1/1/1/1/4 sampling. The comparison does not assume a positive outcome.

## T — test

Construction-only seed 73194101 is excluded from formal use. Formal seed 73194109 generates a disjoint 128-row support pool and 256-row held-out candidate pool using the exact #4792 `protocol.py`. The selected 64-row held-out set has eight rows per class: set, save, toggle, four YIELD reasons, and NO_ACTION already-satisfied. Each arm contains 32 rows; both use the same model/tokenizer snapshot, intent rendering, binder/simulator, LoRA initialization, rank 8, q_proj/v_proj, batch 2, 16 AdamW steps at 2e-4, deterministic flags and greedy decoding. Only support row selection differs.

Run a single offline pinned Docker orchestration on the RTX 3080 after all hash, collision, empty-output and idle-GPU gates pass. Source/model/input mounts are read-only; CPU, memory, PID and temp storage are bounded. Run one independent CPU-only raw audit and the five frozen corruption controls. No retry, replacement seed, or post-result tuning.

## D — decision

PASS requires independent reconstruction of all three 64-row output arms, all 5/5 corruption controls rejected, balanced exact intent/effect >=80% and >=15 percentage points above both imbalanced and base, exact 8/8 in every semantic class, zero forbidden/stale/unauthorized simulated effects, trusted current-state scope/generation binding, each fit <=300 seconds, peak CUDA <=12 GiB and balanced p95 <=1.2 seconds. Provenance/audit mismatch => STOP; resource miss => HOLD_LOCAL_ENVELOPE; integrity-valid quality miss => FAIL_BALANCED_SUPPORT_GATE.

## C — controls

Both arms share fresh pool and held-out input bytes, base weights and tokenizer, prompt/target, parser/binder/simulator, model seed and initial adapter hash, optimizer, rank, batch, step count and decoding. The independent auditor imports no candidate implementation.

## U — limits

One paired synthetic study with one cached Qwen2.5-0.5B-Instruct snapshot on one RTX 3080 Laptop GPU. No live GUI/Astra, production authority, deployed adapter, task-success or cross-model/device claim.

## Pre-fit gates and terminal policy

- Tests and source manifest pass inside the pinned offline image.
- Runner and auditor schema accesses match FREEZE.json; CPU preflight-only run returns fit count 0 and writes its receipt before any GPU/model load.
- GitHub-readback freeze file's actual saved-byte SHA-256 is represented by FREEZE.sha256; local source-mounted freeze verifies against the same digest.
- Formal dataset/model/source hashes, seed/path collision searches, absent fresh result paths and fresh idle RTX 3080 check pass.
- Any STOP is terminal. Do not edit and relaunch this allocation. Record exact command, raw trace and fit counter on GitHub.