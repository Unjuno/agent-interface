# Issue #8406 T1 A10 — canonical claim and scoped-transition audit

## Allocation delta

A09 was stopped after the first consolidation expanded one episode into multiple claims with duplicate IDs. A10 is a fresh allocation with fresh seeds and no A09 output reuse. It specifies one canonical claim per general input episode kind, while preserving generic carry-forward and context-scoped conflict requirements. It names no fixture IDs, source IDs, fact keys, or values.

**H.** On the fixed synthetic episode corpus, consolidation cadence can change exact held-out answers even when memory updates preserve canonical source-bound claims, exceptions, contextual contradictions, and history deltas.

**T.** Same six episode ledger, five queries, checkpoints 1–6, four schedules, fresh seeds 5001/5002/5003; 360 query + 30 consolidation calls, max 390. Same Qwen3:8B digest and decoding as A09. A05–A09 output is excluded.

## Frozen generic claim mapping

- `common_success`: one claim using exact_effect as key/value; ignore other metadata.
- `rare_exception`: one claim containing exact and forbidden effects with its source.
- `fact_observation`: one claim from fact_key/value.
- `history_pair`: one history_delta claim keyed by version plus paired field, with full baseline-to-current value.
- Copy all previous claims unchanged; one episode must not create duplicate claim IDs.
- Conflicts may arise only from fact observations sharing the same key and subject/applicability context with differing values. Keep both observations and add one UNKNOWN conflict only after both are visible. Never treat different action/effect claims as conflicts.
- The frozen auditor checks every transition and query row. Any failed transition, provenance, or raw gate is `FAIL_METHOD`; no schedule conclusion is allowed.

Static prompt contains no fixture IDs, source IDs, keys, or values; construction tests enforce this.

Model: Qwen3:8B digest `500a1f067a9f782620b40bee6f7b0c89e17ae61f686b92c24933e4ca4b2b8b41`, Ollama 0.40.0, distinct private store and loopback service port 11435. First formal request loads model; no warmup generation. Tag and runner identity checked before/after every call. `think:false`, `format=json`, temperature 0.2, top_p 0.9, paired seed, num_ctx8192, query cap128, consolidation cap2048. No retries.

**Primary endpoint.** Exact classification, answer and unique source-ID set at every prefix. Cost endpoints include all calls, tokens, and elapsed inference time.

**Decision.** Scoped sensitivity PASS requires a consistent >=0.10 pairwise exact-accuracy contrast across all three seeds and every transition/raw/method gate passing. No-material PASS requires every contrast below 0.10 and all gates passing. Failed method/transition gate is `FAIL_METHOD`; otherwise `UNCERTAIN`. No production policy claim.

**C / U.** Schema and prompt compliance affect results. Evidence remains limited to this one synthetic corpus, selected queries, one model/quantization, and three seeds.

## One-shot execution

Run ten construction tests before freeze. Candidate once to exclusive raw. Auditor once only after complete successful 390 calls. Preserve partial raws and STOPs; no retries, prompt edits, schedule tuning, or predecessor pooling.
