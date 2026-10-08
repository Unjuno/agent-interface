# Issue #8406 T1 A07 — evidence-bounded transition-audited cadence evaluation

## Allocation delta

A06 completed but its frozen auditor found premature conflicts at prefix 4. Root cause: the consolidation prompt itself named future source IDs and values, so it leaked ep05 before that episode was visible. A07 uses a new allocation and seeds, excludes all A06 model output, and replaces fixture-specific prompt instructions with generic evidence-bounded rules. The frozen auditor retains exact transition checks and a construction test rejects known future-fixture literals in the static consolidation template.

**H.** On a fixed synthetic episode corpus, consolidation cadence can change exact held-out answers even when every derived-memory transition is required to preserve source-bound exceptions, explicit conflicts only after evidence appears, and complete history deltas.

**T.** Same six episode ledger, five held-out queries, checkpoints 1–6, four schedules, fresh seeds 4701/4702/4703. 360 query calls and 30 consolidation calls, maximum 390. Same Qwen3:8B digest, decoding, query cap and 2048 consolidation cap as A06. A06 and A05 outputs are excluded.

## Frozen transition contract

- Carry every supplied/prior fact forward, with no unreferenced episode or source and no lost episode.
- Represent an episode containing exact and forbidden effects with both values and the exact source.
- For same-key observations with different values, preserve each observation and add an `UNKNOWN` conflict only after both values occur in supplied or prior memory. Never anticipate unseen evidence.
- For a supplied baseline/current pair, preserve the full `<baseline>-><current>` value and exact pair of source IDs.
- The independent auditor checks all transitions and answer raw before `PASS_METHOD`; a failed transition gate prevents a cadence conclusion.

The static prompt may state only these generic rules. It must not name fixture-specific episode IDs, source IDs, fact keys, or values. A regression test covers known literals from this ledger.

Model: Qwen3:8B digest `500a1f067a9f782620b40bee6f7b0c89e17ae61f686b92c24933e4ca4b2b8b41`, Ollama 0.40.0, a private store on loopback port 11435. The distinct private store contains the existing manifest and five content-addressed blobs, SHA-256 verified and hardlinked. The shared daemon/model store is unchanged. First formal request loads the model; no warm-up call. Tag and runner identity are checked before/after each request. `think:false`, `format=json`, temperature 0.2, top_p 0.9, paired seed, num_ctx 8192, query cap 128, consolidation cap 2048. No retries.

**Primary endpoint.** Exact classification, answer and unique source-ID match at every prefix, 30 query rows per seed/arm. Cost endpoints include all calls, actual tokens and elapsed inference milliseconds.

**Decision.** `PASS_CADENCE_SENSITIVITY_SCOPED` only if a pairwise exact-accuracy difference is at least 0.10 with consistent direction over all three seeds and every raw, transition and method gate passes. `PASS_NO_MATERIAL_CADENCE_EFFECT_SCOPED` only if all differences stay below 0.10 and all gates pass. Failed transition or method gate is `FAIL_METHOD`; otherwise `UNCERTAIN`. No result authorizes a deployed memory policy.

**C / U.** Prompt representation can affect memory quality. Results remain limited to one synthetic ledger, selected questions, one model/quantization and three seeds; they do not establish deployed GUI behavior or safety.

## One-shot execution

Run seven construction tests before freeze. Candidate runs once to an exclusive raw path. Auditor runs once only after candidate exit zero and 390 complete rows. Preserve all raw and logs. No retries, prompt/schedule edits, or output pooling from predecessor allocations.
