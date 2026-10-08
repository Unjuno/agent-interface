# Needle LoRA pilot 02 — Issue #3441

## H / T / D / C / U

- **H:** A rank-2 LoRA update can learn a bounded new skill quickly while preserving the old skill. Preregistered acceptance required update <500 ms, old and new held-out accuracy >=0.90, immutable base, and YIELD on invalid intent/scope/evidence. Pilot-02 did not change these criteria.
- **T:** `runner.py` is the source used for this allocation (SHA-256 `8B5C23E187465037A291E180E8002FA6BBDE0E1CB80373868EA7CA046AE066FF`). Seed 3441; PyTorch 2.5.1+cu121, CUDA 12.1, RTX 3080 Laptop GPU (16 GiB); 8 features, hidden 16, 4 classes; 512 base rows, 16 adaptation rows, 4,096 held-out rows per skill; rank-2 LoRA, 120 AdamW steps. Full fine-tune is the comparison arm.
- **D:** Scoped pass required all preregistered gates. The recorded outcome is `FAIL_OLD_SKILL_PRESERVATION`: LoRA update 134.4858 ms and new accuracy 0.922607, but old accuracy 0.043457. Base remained immutable; exact metadata proposed and stale epoch/wrong intent/wrong scope yielded. Full fine-tune reached new 0.27295 / old 0.67212.
- **C:** Same frozen base, seed/data, support set, steps, optimizer family, evaluation set, and host; update method differs. Skill A vs B differs by one-bit label remapping. Gate is deterministic, not learned.
- **U:** One synthetic seed and task; no vision, GUI, real action, multi-task distribution, adapter serialization/reload, rollback test, or general forgetting estimate. The five-block latency summary is not a statistically meaningful p95; WDDM peak-memory APIs unavailable. The Docker attempt stopped on content-store blob I/O errors; this host GPU fallback is not a container pass.

## Disposition

Do not promote to general online-learning or GUI-control claims. Next allocation should compare globally applied adapter against explicit per-skill dispatch (old skill -> frozen base; new skill -> named adapter), test unknown/stale route YIELD, and exercise snapshot switch/rollback. Freeze a new source hash and thresholds before running. Preserve pilot-01 STOP and pilot-02 FAIL as historical records.

Reproduction is intended for a healthy isolated CUDA container, but this exact allocation has already run once and must not be silently rerun as the same formal allocation. A container reproduction is a separately identified successor allocation.

## Evidence links

- [Issue #3441 preregistration and result](https://github.com/Unjuno/agent-interface/issues/3441)
- [runner.py](runner.py)
- [RESULT.json](RESULT.json)
