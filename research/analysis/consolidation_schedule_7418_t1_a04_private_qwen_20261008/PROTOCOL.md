# Issue #8406 T1 A04 — private Qwen model evaluation

## Allocation delta and hypothesis

A01–A03 Gemma attempts ended in identity STOPs; their partial outputs remain separate and are not inputs to this allocation. A04 uses a private Ollama model store and service on loopback port 11435, containing only the existing Qwen3:8B manifest and content-addressed blobs. The private store uses hard links to the already installed blobs; the default Ollama service and its model store are not changed.

**H.** On the same six verified synthetic episodes and at identical query checkpoints, changing when derived memory is rewritten can change exact held-out answers and transition cost for one fixed local model. No direction is assumed.

**T.** Same fixed ledger, five queries, checkpoints 1–6, four schedules, and fresh seeds 4401/4402/4403. Each seed/schedule/checkpoint executes all five queries (360); model consolidation uses 0/6/3/1 updates per seed by arm (30); maximum 390 calls. Episodic-only sees raw episodes through the current prefix; consolidated arms see only memory available at that checkpoint. No GUI, action, user data, or deployed writeback.

Frozen model: Qwen3:8B, digest `500a1f067a9f782620b40bee6f7b0c89e17ae61f686b92c24933e4ca4b2b8b41`, Ollama 0.40.0. Request name `qwen3:8b`. Every generation sets `think:false`, `format=json`, temperature 0.2, top_p 0.9, paired seed, num_ctx 8192, and query/consolidation caps 128/256. Private `/api/tags` must contain exactly this model/digest before and after each request. `/api/ps` may be empty only before the first request; thereafter it must contain exactly one runner at that digest, including after every generation. Both tag and runner identity are recorded per request. Candidate preserves raw immediately and stops on any identity change. No retries.

First request loads the model and is part of the formal candidate allocation; no model generation or warm-up is permitted before freeze.

**Primary endpoint.** Exact classification, answer, and unique source-ID set match to preregistered gold tuple at each prefix, summarized over 30 query rows per seed/arm. **Cost endpoints:** all model calls including consolidation, prompt/completion tokens, and elapsed inference milliseconds. Actual token use is retained; no UI latency or monetary inference.

**Decision.** `PASS_CADENCE_SENSITIVITY_SCOPED` if a pairwise exact-accuracy difference is at least 0.10 and has the same direction across all three seeds, with clean independent raw-only audit. `PASS_NO_MATERIAL_CADENCE_EFFECT_SCOPED` if all pairwise differences are below 0.10 for all seeds and audit passes. Otherwise `UNCERTAIN`; row, raw, or model identity failure is `FAIL_METHOD`. No result authorizes a deployed policy.

**C.** Differences may reflect summary quality, actual evidence-token volume, or authored query choices rather than cadence path dependence alone. Episodic retrieval may simply be more direct.

**U.** One synthetic corpus, one model family/quantization, and three seeds do not establish real GUI behavior, safety, prevalence, or optimal cadence.

## One-shot execution

Run the frozen construction tests before freeze. Candidate runs once to an exclusive raw JSONL path. Run the independent auditor once only after candidate exit zero and exactly 390 complete rows. No retries, post-launch tests, mutation probes, or schedule changes. Preserve all partial raw/STOP evidence.
