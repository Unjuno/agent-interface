# Issue #4505 fresh-seed local CUDA replication preregistration

## H / T / D / C / U

**H** — Using the exact #4492 runner, independent auditor, and training procedure at a fresh seed, all routed A/B/C tasks meet the 0.90 held-out accuracy gate, at least one shared B/C control remains below 0.90, and result serialization plus route/state integrity remain auditable. This is one independent replication only, not a population estimate.

**T** — Allocation `needle-lora-3441-pilot-04f-seed-replication-20260926-01`; seed 777731; base `eb87f1f36871fdc483521f09094923a12409c933`; branch `research/needle-lora-3441-pilot-04f-20260926`; additive path `research/needle_lora_3441_pilot_04f_seed_replication_v1/`. Dataset seeds 777732–777737; initialization/training seeds 777741–777754. Preserve #4492's architecture and procedure exactly: 8 features, hidden-16 tanh core, four classes, rank-2 output adapter; 512 base rows / 400 base updates; 16 support rows each for B/C; 4,096 held-out rows per skill; 120 updates per adapter fit; AdamW LR .04, batch 32; same deterministic CUDA settings, adapter ordering, route controls, full-state snapshot/rollback and row audit. Only treatment change is fresh seed and allocation identity. No threshold/hyperparameter/scorer changes. Source/program/test edits are seed/path/identity-only; verify diff before freeze.

Construction must remain training-free. It verifies fixed 400/120 update schema, deterministic datasets, route identity, invalid-route YIELD, full-state roundtrip/rollback, auditor recomputation/corruption controls and frozen source pins. Freeze all source/test/prereg hashes before the one formal run.

**D** — `PASS_MULTI_SKILL_ROUTING_REPLICATED_SCOPED` iff routed A/B/C each >=0.90, at least one shared B/C <0.90, invalid routes all YIELD, base immutable, full-state snapshot/rollback exact, and independent row-level audit has zero errors. `HOLD_NO_ROUTING_ADVANTAGE` if routed quality and integrity pass but shared B and C are both >=0.90. `FAIL_MULTI_SKILL_INTERFERENCE` for integrity-valid routed miss. Typed `FAIL` for route/state/audit integrity; typed `STOP` for environment/source/serialization/provenance ambiguity. Exactly one formal invocation; no retry, tuning, seed substitution or result reconstruction.

**C** — Windows host CUDA only: NVIDIA RTX 3080 Laptop, Python 3.11.9, PyTorch 2.5.1+cu121, CUDA 12.1. Set `CUBLAS_WORKSPACE_CONFIG=:4096:8` before startup; deterministic algorithms on, TF32 off. Require >=1 GiB free C: and >=2 GiB free VRAM at launch. No container claim, cloud/HF Jobs, package installation, image pull, network/provider, GUI/input or runtime authority. Peak CUDA memory is typed `UNAVAILABLE_WDDM`.

**U** — One additional seed in one small synthetic family. This does not estimate population reliability or establish realistic transfer, GUI utility, action safety, latency, crash-safe persistence or runtime promotion. Preserve #3895/#4471/#4492 evidence independently; do not pool outcomes or choose seeds based on results.

## Source identity

Canonical UTF-8/LF SHA-256 and Git blob pins for runner, auditor, tests, and this preregistration are recorded in `FREEZE.json`.
