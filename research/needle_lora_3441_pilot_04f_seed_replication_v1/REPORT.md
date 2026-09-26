# 04f fresh-seed local CUDA LoRA replication

## H / T / D / C / U

**H** — Test whether the scoped #4492 routed-vs-shared LoRA result and its serialization/integrity gates hold at one independent fresh seed. This is a single replication, not a population estimate.

**T** — Allocation `needle-lora-3441-pilot-04f-seed-replication-20260926-01`; seed 777731; additive path `research/needle_lora_3441_pilot_04f_seed_replication_v1/`; source branch `research/needle-lora-3441-pilot-04f-20260926`. One Windows-host RTX 3080 Laptop run, Python 3.11.9 / PyTorch 2.5.1+cu121 / CUDA 12.1. The source and decision protocol match #4492; only seed and allocation identity differ. Exactly one formal invocation, no retry/tuning.

**D** — `PASS_MULTI_SKILL_ROUTING_REPLICATED_SCOPED`. Runner exit 0; stdout 817,026 bytes; stderr empty. Independent CPU auditor exit 0, errors=[], 24,576 predictions recomputed. Routed accuracy A 0.957275, B 0.929932, C 0.915771 (all >=0.90). Shared sequential accuracy A 0.093506, B 0.001465, C 0.886719 (at least one shared B/C <0.90). Six invalid routes all YIELD; base immutable; full-module snapshot roundtrip and rollback tensor-exact. Base training 400 steps; each adapter fit 120. Peak CUDA memory is `UNAVAILABLE_WDDM`.

**C** — This is one extra seed in the same small synthetic family. It does not estimate population reliability or establish realistic transfer, GUI utility, action safety, latency, persistence, or runtime promotion.

**U / lineage** — This reproduces the scoped threshold result once; broader independent families/tasks are still needed. #3895, #4471 and #4492 remain distinct, unchanged evidence.

## Evidence

- Raw formal stdout: `FORMAL_STDOUT.json`; SHA-256 `74e72f96e29ddbed9891b8b7bf10c67caf83d6de2e251c390c95851f1bdf7894`.
- Empty stderr SHA-256: `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`.
- Independent audit: `AUDIT.json`; detailed environment and hashes: `FORMAL_METADATA.json`.
- Frozen source/preregistration pins: `FREEZE.json`; preformal gate: `PREFLIGHT.json`.
- Construction/auditor suite: 17/17 PASS before formal execution.
