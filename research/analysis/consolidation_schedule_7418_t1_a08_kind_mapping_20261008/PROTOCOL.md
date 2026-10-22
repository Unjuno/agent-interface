# Issue #8406 T1 A08 — generic kind-mapped transition-audited cadence evaluation

## Allocation delta

A07 was stopped after its generic prompt returned a claim kind outside the frozen schema. A08 is a fresh allocation with fresh seeds and no A07 output reuse. It adds only a generic mapping from input episode kinds to allowed memory claim kinds. It still contains no fixture IDs, sources, fact keys, or values. The same transition-gated auditor and future-literal regression remain frozen.

**H.** On a fixed synthetic episode corpus, consolidation cadence can change exact held-out answers while every derived-memory transition preserves source-bound evidence, exceptions, explicit conflicts only after evidence appears, and full history deltas.

**T.** Same six episode ledger, five held-out queries, checkpoints 1–6, four schedules, fresh seeds 4801/4802/4803. 360 query calls plus 30 consolidation calls; max 390. Same Qwen3:8B digest and decoding as A07. A05–A07 outputs are excluded. The sole experimental protocol delta is the generic kind mapping: `common_success` maps to `verified_pattern`; `rare_exception` to `forbidden_effect_exception`; `fact_observation` to `fact_observation`; `history_pair` to `history_delta`.

## Frozen transition contract

- Carry all supplied/prior facts forward with exact source IDs and no invented/future claims.
- Keep both exact and forbidden effects when an input episode has both.
- Keep same-key differing observations separate and add an UNKNOWN conflict only after both values are present.
- For a supplied baseline/current pair, preserve full `<baseline>-><current>` relation and exact source IDs.
- Auditing all transition states is required before a cadence result; failed transition gates are `FAIL_METHOD`.

Model: Qwen3:8B digest `500a1f067a9f782620b40bee6f7b0c89e17ae61f686b92c24933e4ca4b2b8b41`, Ollama 0.40.0, distinct private store and loopback service 11435. First formal request loads the model; no warm-up. Tag and running digest gates apply before/after every call. `think:false`, `format=json`, temperature 0.2, top_p 0.9, paired seed, num_ctx 8192, query cap 128, consolidation cap 2048. No retries.

**Primary endpoint.** Exact classification, answer, and unique source-ID match at each prefix across 30 query rows per seed/arm. Costs include all model calls, actual token counts and elapsed inference time.

**Decision.** `PASS_CADENCE_SENSITIVITY_SCOPED` only with a same-direction pairwise exact-accuracy contrast of at least 0.10 across all seeds and every raw/transition/method gate passing. `PASS_NO_MATERIAL_CADENCE_EFFECT_SCOPED` only with every contrast below 0.10 and all gates passing. Failed transition/method gate is `FAIL_METHOD`; otherwise `UNCERTAIN`. No outcome authorizes a deployed memory policy.

**C / U.** Prompt/schema design may affect behavior; evidence is limited to one synthetic corpus, chosen queries, one model/quantization and three seeds. No production GUI/safety claim.

## One-shot execution

Run eight construction tests before freeze. Candidate runs once to an exclusive raw path. Auditor runs once only after candidate exit zero and 390 complete rows. Preserve raw/logs. No retries, prompt/schedule edits, or pooling predecessor outputs.
