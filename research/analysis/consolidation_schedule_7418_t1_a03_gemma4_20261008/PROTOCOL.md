# Issue #8406 T1 A03 — loaded-runner identity evaluation

## Allocation delta and H / T / D / C / U

This is a fresh A03 allocation after T1 A01 and A02 terminal STOPs, whose partial raws remain separate and unused. Both STOPs found mutable duplicate names in `/api/tags`; A02 nevertheless showed that `think:false` produces JSON answers. A03 therefore verifies the **loaded runner** through Ollama v0.40.0 `GET /api/ps` before and after every generation, recording its exact digest and requiring `c6eb396dbd5992bbe3f5cdb947e8bbc0ee413d7c17e2beaae69f5d569cf982eb` on both sides. The official API defines `/api/ps` as listing models loaded into memory and returns each running model's digest. No generation is allowed unless the exact runner is already present before candidate start.

**H.** On the same six verified synthetic episodes and at identical query checkpoints, changing when derived memory is rewritten can change exact held-out answers and transition cost for one fixed local model. No direction is assumed.

**T.** Same fixed ledger, five queries, checkpoints 1–6, four schedules, and fresh seeds 4301/4302/4303. Each seed/schedule/checkpoint executes all five queries (360); model consolidation uses 0/6/3/1 updates per seed by arm (30); maximum 390 model calls. Episodic-only sees raw episodes through the current prefix; consolidated arms see only memory available at that checkpoint. No GUI, action, user data, or deployed writeback.

Frozen model boundary: request name `gemma4:e4b`, loaded runner digest `c6eb396dbd5992bbe3f5cdb947e8bbc0ee413d7c17e2beaae69f5d569cf982eb`, 8.0B Q4_K_M, Ollama 0.40.0. Every generation sets `think:false`, `format=json`, temperature 0.2, top_p 0.9, paired seed, num_ctx 8192, and query/consolidation caps 128/256. The runner checks `/api/ps` immediately before and after every request, writes full request/response/timing/token raw after each request, and stops on any identity change. No retries.

**Primary endpoint.** Exact classification, answer, and unique source-ID set match to the preregistered gold tuple at each prefix, summarized over 30 query rows per seed/arm. **Cost endpoints:** all model calls including consolidation, prompt/completion tokens, and elapsed inference milliseconds. Actual token use is retained; no UI latency or monetary inference.

**D.** `PASS_CADENCE_SENSITIVITY_SCOPED` if a pairwise exact-accuracy difference is at least 0.10 and has the same direction across all three seeds, with clean independent raw-only audit. `PASS_NO_MATERIAL_CADENCE_EFFECT_SCOPED` if all pairwise differences are below 0.10 for all seeds and audit passes. Otherwise `UNCERTAIN`; row, raw, or loaded-model identity failure is `FAIL_METHOD`. No result authorizes a deployed policy.

**C.** Differences may reflect summary quality, actual evidence-token volume, or authored query choices rather than cadence path dependence alone. Episodic retrieval may simply be more direct.

**U.** One synthetic corpus, model family/quantization, and three seeds do not establish real GUI behavior, safety, prevalence, or optimal cadence.

## One-shot execution

Run construction tests before freeze. The candidate CLI runs once to an exclusive raw JSONL path. Run the independent auditor once only after candidate exit zero and exactly 390 complete rows. No retries, post-launch tests, mutation probes, or schedule changes. Preserve all partial raw/STOP evidence.
