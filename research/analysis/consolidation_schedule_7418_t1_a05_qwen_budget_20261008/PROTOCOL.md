# Issue #8406 T1 A05 — Qwen consolidation-output budget test

## Why this fresh allocation exists

T1 A04 was a terminal method STOP: at the first six-episode per-episode consolidation, Ollama reported `done_reason=length` and `eval_count=256`, and the JSON response was truncated. That allocation remains frozen with raw output and is not resumed, repaired, audited, or scored. A05 addresses this specific output-budget failure with a fresh allocation, fresh paired seeds, and a 2048-token consolidation cap. The corpus, queries, arms, checkpoints, prompt, model digest, decoding, and decision rule remain fixed. No A04 answer or memory output is used.

## Hypothesis and design

**H.** On the same six verified synthetic episodes and fixed query checkpoints, changing when derived memory is rewritten can change exact held-out answers and transition cost for one fixed local model. No direction is assumed.

**T.** Same frozen ledger, five queries, checkpoints 1–6, four schedules, fresh seeds 4501/4502/4503. Each seed/schedule/checkpoint executes all five queries (360); model consolidation uses 0/6/3/1 updates per seed by arm (30); maximum 390 calls. Episodic-only sees raw episodes through the current prefix; consolidated arms see only memory available at that checkpoint. No GUI, action, user data, or deployed writeback.

Model: Qwen3:8B, digest `500a1f067a9f782620b40bee6f7b0c89e17ae61f686b92c24933e4ca4b2b8b41`, Ollama 0.40.0, private model store on loopback port 11435. The store contains only the existing model manifest and hardlinks to its content-addressed blobs. The shared daemon/model store is unchanged. Every generation uses `think:false`, `format=json`, temperature 0.2, top_p 0.9, seed paired within schedule, num_ctx 8192, query output cap 128, and consolidation cap 2048. Private `/api/tags` must contain exactly the frozen model/digest before and after every request. `/api/ps` may be empty before first request only; after the first request exactly one runner at the frozen digest is required before/after every call. Identity checks are recorded on every request. No retries. The first request loads the model as part of the formal candidate; no warm-up generation occurs before freeze.

**Primary endpoint.** Exact classification, answer and unique source-ID set match against preregistered gold at every prefix, summarized over 30 query rows per seed/arm. Cost endpoints are model calls including consolidation, prompt/completion tokens, and elapsed inference milliseconds.

**Decision.** `PASS_CADENCE_SENSITIVITY_SCOPED` if any pairwise exact-accuracy difference is at least 0.10 and has the same direction across all three seeds, with clean independent raw-only audit. `PASS_NO_MATERIAL_CADENCE_EFFECT_SCOPED` if all pairwise differences are below 0.10 for all seeds and audit passes. Otherwise `UNCERTAIN`; method, raw, or identity failure is `FAIL_METHOD`. No result authorizes a deployed memory policy.

**C.** Differences may reflect summary quality, evidence-token volume, or authored query choices, not cadence path dependence alone. Episodic retrieval may simply be more direct. **U.** One synthetic corpus, model/quantization, and three seeds do not establish GUI behavior, safety, prevalence, or optimal cadence.

## One-shot execution

Run construction tests before freeze. Candidate runs once to exclusive raw JSONL. Auditor runs once only after successful candidate exit and 390 complete rows. No retries, schedule changes, or pooling of any predecessor outputs. Preserve every partial raw and terminal STOP.
