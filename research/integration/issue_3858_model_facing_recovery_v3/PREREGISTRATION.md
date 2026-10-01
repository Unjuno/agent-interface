# Issue #3858 — model-facing epoch-composition successor v3

Allocation: `issue3858-model-facing-recovery-orbstack-01`
Base main: `688e45cb99af4af7cc71db77049b5a6135a2f36f`
Path: `research/integration/issue_3858_model_facing_recovery_v3/`
Predecessor v2 STOP: #3204 allocation 02 / PR #3823; preserved unchanged.

## H / T / D / C / U

- **H:** With valid PNG scanline filters and Ollama JSON mode, the frozen typed epoch-aware policy returns the exact oracle on coherent and within-bound same-epoch evidence, rejects cross-epoch conflict before inference, and yields more exact answers than the zero-skew-only rejector. Other policies are comparison controls, not trusted authorities.
- **T:** Reproduce the exact three scenarios and four policy semantics from #3204 v2: aligned; same-epoch 40 ms bounded skew with a 50 ms bound; cross-epoch conflict with a late duplicate state. Twelve policy/scenario rows; exactly nine model-eligible cells. Preserve raw PNGs, every request/response, bridge receipts, answer, disposition, call and timing/token data. Correct PNG filter byte from 255 to 0 and API `format` from JSON Schema object to literal `"json"`, based on the retained STOP chain #3204 v2 → #3827 → #3843. No GUI, action or effect.
- **D:** `PASS_MODEL_FACING_EPOCH_COMPOSITION_SCOPED` iff the complete 12-row/9-call grid is source- and model-bound; every candidate answer exactly matches its oracle; candidate conflict abstains before inference; candidate exact count exceeds `EPOCH_REJECT_ONLY`; PNG, byte-link, provenance, model identity, audit, and corruption controls all pass. Wrong candidate answer or unsafe conflict disposition is FAIL. Transport, model, container, provenance, integrity, incomplete-grid, or audit error is STOP/HOLD as recorded. Formal invocation 1, request ceiling 9, retries 0, post-freeze edits 0.
- **C:** Obstac/OrbStack; pinned `linux/arm64` image `issue3204-epoch-composer@sha256:6a3bb69f7ab1e386ca0fd6421c7194024fd9acd2978d168a5b877949c890fa51`; context `orbstack`; `--network none`; read-only root/source; dedicated output/RPC mounts; checked `OBSTAC_SOURCE_COMMIT`, `OBSTAC_IMAGE_ID`, `OBSTAC_FREEZE_SHA256`. Only a frozen host bridge may connect to `127.0.0.1:11434`; it uses JSON mode and persists exact success or HTTPError status/headers/body, with no retries. Ollama 0.34.2; `qwen2.5vl:7b`, digest `5ced39dfa4bac325dc183dd1e4febaa1c46b3ea28bce48896c8e69c1e79611cc`; temperature 0, seed 3204, max 32 tokens.
- **U:** This is only the original three-case model-facing first rung. It does not close #3204's held-out channel matrix or establish general multimodal reasoning, GUI correctness, recovery benefit, production reliability, or efficiency. The corrected-input result #3843 is a single compatibility point. All predecessor STOP bytes remain immutable.

## Frozen cases and oracle

1. `aligned`: image/UI-tree/state task-A, epoch 4, green/READY; capture skew 0 ms. Expected `READY`.
2. `bounded_skew`: same task/epoch 7, green/READY; captures 200/230/240 ms; skew 40 ms ≤ 50 ms. Expected `READY`; `EPOCH_REJECT_ONLY` abstains.
3. `cross_epoch_conflict`: red/BLOCKED image at epoch 8; UI-tree/state READY at epoch 9; duplicate old BLOCKED state at epoch 8 arrives last. Expected `ABSTAIN`; typed candidate and reject-only must abstain before model. The latest and best-effort controls receive the frozen merged evidence.

Policy algorithms and text/prompt contract are carried forward verbatim in intent from the v2 frozen allocation; the source is independently reimplemented in this additive path and hash-frozen here. No policy or prompt tuning after formal start.
