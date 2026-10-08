# Issue #8406 T1 A13 — schema-constrained output format

## Rationale and delta

A12 completed 390 calls after an isolated model-store identity preflight, then failed its transition audit with 18 violations: 12 per-episode states used input kind `rare_exception` instead of output kind `forbidden_effect_exception`; 6 final batch-2 violations reflected a missing conflict claim. Terminal consolidation emitted both required claims correctly. The static prompt was the same across those arms. This suggests the output-format interface may contribute to enum drift, while conflict completeness is a separate semantic issue.

Ollama v0.40.0 accepts a JSON value for the `/api/generate` `format` field, and Ollama's structured-output documentation specifies JSON Schema as a constrained response format. A13 supplies a schema with required claim fields and an enum of allowed claim kinds. The prompt text, corpus, queries, schedule logic, model, decoding, call budget, and auditor contract stay as in A12. Query requests remain `format=json`. The only intended change is the consolidation `format` from JSON mode to the frozen JSON Schema. This constraint guarantees neither correct episode-to-kind mapping nor the presence of a conflict claim; those remain audited.

**H.** On this corpus/model, supplying the allowed claim-kind enum as a structured-output schema will prevent the invalid output kind `rare_exception` seen in A12. Whether all transition claims become faithful remains separately determined by the auditor.

**T.** Four schedules, six prefixes, five fixed queries, seeds 5301/5302/5303; 360 query plus 30 consolidation calls, 390 maximum. Qwen3:8B frozen digest, Ollama v0.40.0, distinct private store/server, same decoding and prompts as A12. Run the read-only model/store preflight first. Candidate rechecks identity around each request. No warmup, retries, GUI, user data, or action authority.

**D.** The inherited cadence endpoint requires a consistent >=0.10 paired contrast across all three seeds and a clean transition/raw audit. All contrasts within margin plus all gates clean permits scoped no-material result. Any failed method/transition gate is `FAIL_METHOD`; otherwise `UNCERTAIN`. A13 also reports the preregistered schema-compliance diagnostic: count of output claims with kind outside the allowed enum. It is not a replacement for full transition audit or cadence endpoint.

**C/U.** Structured output constrains shape and enum but not correct semantic mapping, provenance, claim completeness, or conflict derivation. Results remain limited to the synthetic fixture, queries, model and local software version.

## One-shot boundary

Run construction and identity preflight checks before freeze/formal generation. Candidate once; auditor once only after complete 390-call raw. Preserve all outputs. No repair, retry, or predecessor pooling.

## Primary implementation references

- Ollama v0.40.0 API request type: <https://github.com/ollama/ollama/blob/v0.40.0/api/types.go>
- Ollama structured-output documentation: <https://ollama.com/blog/structured-outputs>
