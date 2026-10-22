# Issue #8406 T1 A09 — context-scoped, no-loss transition audit

## Allocation delta

A08 was stopped after the model dropped earlier claims and treated equal field labels from different actions/contexts as a contradiction. A09 is a fresh allocation with fresh seeds and no A08 output reuse. The generic prompt now requires unchanged prior-claim carry-forward, restricts conflicts to same-key fact observations in the same subject/applicability context, and derives history keys from supplied version/field values. No fixture-specific IDs or values are added to the prompt.

**H.** On a fixed synthetic episode corpus, consolidation cadence can change exact held-out answers while memory transitions preserve source-bound facts, exceptions, contextual conflict distinctions, and complete history deltas.

**T.** Same six episode ledger, five queries, checkpoints 1–6, four schedules, seeds 4901/4902/4903; 360 query + 30 consolidation calls, max 390. Same Qwen3:8B frozen digest, private serving boundary, and decoding as A08. A05–A08 outputs are excluded. The only planned protocol changes are generic carry-forward and applicability-scoped conflict rules, with history key derived from version and field.

## Frozen transition contract

- Map generic input kinds to allowed claim kinds; preserve every prior claim unchanged and add new evidence without dropping earlier claims.
- Preserve exact and forbidden effects with exact source IDs.
- Only fact observations can conflict; require same key, same subject/applicability context and differing values. Preserve both observations; add UNKNOWN conflict with exact union of sources only once both are visible. Common effects from distinct action/context observations are not contradictions.
- For history pairs, derive `<version>-<field>` key and full `<baseline>-><current>` value from the supplied pair and cite both exact sources.
- Frozen auditor checks every transition before any cadence result. Any failed transition gate is `FAIL_METHOD`.

The static prompt contains generic rules only. Regression tests reject fixture-specific IDs, keys and values and check the generic kind/carry-forward/context rules.

Model: Qwen3:8B digest `500a1f067a9f782620b40bee6f7b0c89e17ae61f686b92c24933e4ca4b2b8b41`, Ollama 0.40.0, distinct private model store and loopback port 11435. Tag and runner digest are checked before/after each request. First formal request loads model. `think:false`, `format=json`, temperature 0.2, top_p 0.9, paired seed, num_ctx 8192, query cap 128, consolidation cap 2048. No retries.

**Primary endpoint.** Exact classification, answer and unique source-ID match at each prefix across 30 query rows per seed/arm. Costs include all calls, tokens and elapsed inference time.

**Decision.** `PASS_CADENCE_SENSITIVITY_SCOPED` only with a consistent >=0.10 contrast in all three seeds and all raw/transition/method gates passing; `PASS_NO_MATERIAL_CADENCE_EFFECT_SCOPED` only within margin and all gates passing; otherwise `UNCERTAIN`, with failed method/transition gates `FAIL_METHOD`. No production or deployed policy claim.

**C / U.** Prompt compliance is part of the tested configuration. Evidence remains bounded to one synthetic corpus, selected questions, one model/quantization and three seeds.

## One-shot execution

Run nine construction tests before freeze. Candidate once to exclusive raw path; auditor once only after complete successful 390-row candidate. No retries, edits, tuning, or predecessor pooling. Preserve all partial data.
