# Issue #8406 T1 A06 — transition-audited Qwen cadence evaluation

## Allocation delta

A05 showed answer-level schedule sensitivity, but a supplemental raw review found the model omitted explicit conflict objects and flattened history-pair values. Its frozen auditor had not enforced the transition requirements in the Issue. A06 is a fresh allocation with fresh seeds and no A05 model output reuse. It strengthens the consolidation prompt and makes source coverage, source-faithfulness, exception preservation, explicit conflict encoding, and history-delta preservation hard gates in the frozen independent auditor.

**H.** On a fixed synthetic episode corpus, consolidation cadence can change exact held-out answers even when memory transitions are required to preserve source-bound exceptions, explicit conflicts, and history deltas.

**T.** Same six episode ledger, five queries, checkpoints 1–6, four schedules, fresh seeds 4601/4602/4603. 360 query calls plus 30 consolidation calls, maximum 390. Same Qwen3:8B frozen digest and 2048-token consolidation cap established by A05. The only planned changes from A05 are fresh seeds and a consolidation prompt that states exact source-bound representations; the independent auditor now checks those requirements at every transition. A05 output is excluded.

## Frozen transition contract

- Every visible episode must have exactly one memory claim with exact source IDs and the preregistered kind/key/value; no episode may be dropped or invented.
- The rare exception `ep03` must remain `forbidden_effect_exception`, with value `effect=no_external_effect; forbidden=publish` and source `src-03`.
- When both revision-r7 observations are present, retain both fact claims and add an explicit `conflict:revision-r7-mode` claim, kind `conflict`, value `UNKNOWN`, source IDs `src-04` and `src-05`. It must not appear earlier or be silently resolved.
- At prefix six, the history claim must be kind `history_delta`, value `draft->published`, and cite both baseline/current source IDs.
- The auditor validates every transition from raw output before it can return `PASS_METHOD`. Missing or unfaithful transition records make the complete candidate result `FAIL_METHOD`, even if answer accuracy contrasts are large.

Model: Qwen3:8B, digest `500a1f067a9f782620b40bee6f7b0c89e17ae61f686b92c24933e4ca4b2b8b41`, Ollama 0.40.0, private model store and loopback port 11435. Fresh private store uses the existing manifest and hardlinks to five SHA-256-verified content-addressed blobs; shared Ollama state remains unchanged. First formal request loads the model. Tag and loaded-runner digest are checked before and after every request. `think:false`, `format=json`, temperature 0.2, top_p 0.9, paired seed, num_ctx 8192, query cap 128, consolidation cap 2048. No retries.

**Primary endpoint.** Exact classification, answer and unique source-ID set match at every prefix, across 30 query rows per seed/arm. **Cost endpoints:** all calls including consolidation, actual prompt/completion tokens, and elapsed inference milliseconds.

**Decision.** `PASS_CADENCE_SENSITIVITY_SCOPED` only when a pairwise exact-accuracy difference is at least 0.10 in the same direction across all three seeds and all source/transition/method gates pass. `PASS_NO_MATERIAL_CADENCE_EFFECT_SCOPED` only when all pairwise differences are below 0.10 and every audit gate passes. Otherwise `UNCERTAIN`; failed transition or method gates are `FAIL_METHOD`. No outcome authorizes a deployed policy.

**C / U.** Prompt compliance and representational schema may affect results; all findings remain limited to one synthetic corpus, model/quantization, selected queries and three seeds. No real GUI behavior, safety, prevalence or optimal cadence is established.

## One-shot execution

Run the six construction tests before freeze. Candidate runs once to a new exclusive raw JSONL path. The frozen auditor runs once only after 390 complete rows and candidate exit zero. Preserve all raw/logs. No retries, prompt changes, schedule tuning, or pooling of prior allocations.
