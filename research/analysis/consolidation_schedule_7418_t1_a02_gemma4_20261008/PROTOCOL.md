# Issue #8406 T1 — frozen local-model schedule evaluation

## Allocation delta and H / T / D / C / U

The `think:false` request field is supported by the pinned [Ollama v0.40.0 API](https://github.com/ollama/ollama/blob/v0.40.0/docs/api.md), which documents both the thinking parameter and structured/JSON output.

This is a fresh A02 allocation after A01 terminal STOP. A01 had three outputs truncated by model thinking and then stopped on a mutable duplicate `gemma4:e4b` tag; its raw and STOP remain unchanged and are not reused. A02 uses new seeds 4201/4202/4203, unique, per-call digest-checked `gemma4:latest` (same frozen digest `c6eb396d…`), and `think:false` per the local Ollama v0.40.0 API. The six-episode corpus and query set remain fixed to preserve the scientific contrast; no A01 output enters A02.

## H / T / D / C / U

**H.** On the same six verified synthetic episodes and at identical query checkpoints, changing when derived memory is rewritten can change exact held-out answers and transition cost for one fixed local model. Episodic-only, per-episode, batch-2, and terminal schedules may differ in answer correctness; no direction is assumed.

**T.** Use the six-episode ledger byte-copied from the T0 A01 input, five preregistered queries, checkpoints 1–6, and three fresh fixed seeds 4201/4202/4203. Each seed/schedule/checkpoint executes all five queries (360 query calls). LLM consolidation itself is part of the intervention: 6 per-episode, 3 batch-2, 1 terminal, and 0 episodic-only updates per seed (30 update calls total). The maximum is 390 calls. Query retrieval is held fixed by schedule: episodic-only sees all raw episodes through the current prefix; consolidated schedules see only the derived memory available at that checkpoint. Consolidation uses only the newly due episodes and prior derived memory. No action, GUI, user data, or deployed memory writeback occurs.

Model/runtime frozen before generation: `gemma4:latest`, Ollama tag digest `c6eb396dbd5992bbe3f5cdb947e8bbc0ee413d7c17e2beaae69f5d569cf982eb`, 8.0B Q4_K_M, Ollama 0.40.0, local `127.0.0.1:11434`; temperature 0.2, top_p 0.9, thinking disabled; seed shared across paired arms within each replicate, num_ctx 8192, query num_predict 128, consolidation num_predict 256, JSON mode (`format=json`), no retries. Model digest is rechecked before every generation. The query prompt, expected labels, and source ledger are fixed files in this package. Raw responses, prompts/options, usage counts, timing, evidence visible at query time, and every consolidation transition are flushed to one exclusive JSONL file after each call. A transport/digest error is retained as a row and terminates the one-shot run without retry.

**Primary endpoint.** Exact query correctness per seed/arm across 30 query rows: classification, answer, and unique source-ID set must all equal the preregistered expected tuple at that prefix. The independent auditor reconstructs the full schedule, visible evidence, prompts, options, model identity, row count, raw JSON, endpoint labels, and paired seed contrasts.

**Cost endpoints.** For every seed/arm, report calls, prompt tokens, completion tokens, and summed wall inference milliseconds, including consolidation calls. Query calls and caps are identical across arms; actual token use is recorded because memory lengths differ. No end-to-end UI latency or monetary cost is inferred.

**D.** `PASS_CADENCE_SENSITIVITY_SCOPED` if any preregistered pairwise schedule contrast differs by at least 0.10 exact-accuracy points (at least 3/30 rows) in the same direction for all three seeds and the independent method audit passes. `PASS_NO_MATERIAL_CADENCE_EFFECT_SCOPED` if all pairwise differences are strictly below 0.10 for every seed and the audit passes. Otherwise `UNCERTAIN`; any missing/misaligned/duplicate row, model drift, invalid raw, or audit failure is `FAIL_METHOD`. No result authorizes a deployed policy.

**C.** The measured difference could arise from summary quality or unequal actual evidence-token volume rather than cadence path dependence alone. Episodic retrieval may simply be more direct. A single model's decoding and the authored query set may dominate.

**U.** One synthetic corpus, one model family/quantization and three decoding seeds cannot establish real GUI memory behavior, prevalence, safety, generalization, or optimal cadence. No GUI, action, task effect, or production system is tested.

## One-shot execution

Construction tests are completed before the freeze commit. After freeze, invoke candidate CLI once to the exclusive raw path. If it exits zero and raw is complete, invoke the separate auditor CLI once. No retry, post-launch test, imported target function, mutation probe, or schedule adjustment is allowed. Preserve a partial raw and terminal failure if any call fails. The local Ollama service is the named model boundary; runner uses no external network host or API.
